"""M12 C1 (item 133): Owen (1975) allocation of the system cost to the 11 countries and the international-bunker account (12th player, item 91).
READ ONLY - Python only, no solver call; the solve results are not changed.

Principle (linear production game, Owen 1975). The integrated LP  min c'x  s.t.  l <= Ax <= u  has right-hand sides that belong to players
(demand at a bus, resource potentials, fixed capacities, country caps). With b(S) = sum_{i in S} b_i the coalition LP has the same matrix and
the dual y* of the grand LP prices every player's rights and obligations; phi_i = y*' b_i + (player's objective constants) is in the core:
phi(S) = y*' b(S) <= max_y {y' b(S): y dual feasible} = c(S) (weak duality), phi(N) = c(N) (strong duality). Cost version used here
(market-settlement form, equal to y*' b_i when every non-nodal row lies inside one player and the KKT conditions hold exactly):

    phi_i = cost of player i's assets (annuity, FOM, VOM, fuel, extra-ASEAN imports, objective constants)
            + value at the nodal duals of the player's net purchases - net sales (every carrier, every bus)
            - sum over cross-border assets l touching i of  s_{l,i} x (rent_l - annuity_l),   s_{l,i} = alpha or 1 - alpha

Main value (supplement 01 D1, item 136): the dual form y'b computed by m12_rhs_audit.py (m12_owen/OWEN.json; in the core by Owen's theorem).
The market-settlement form above equals y'b only without coupling rows: the homogeneous KVL rows of loops with lines of several owners move value
between them (loop transfer), so it is reported alongside, with market - dual = KVL transfer + residual. benefit / loo use the dual form when
the runs have it.

Premises (checked by m12_rhs_audit.py): every right-hand side belongs to a player; a cross-border line is two halves, each country owning its
half (both halves have the full rating, so the line exists only if both countries take part); extra-ASEAN trade at fixed prices; the bunker
demand belongs to no country and is the 12th player. Dual degeneracy: two half-rows with the same coefficients carry any split of the line's
shadow value, so every alpha in [0, 1] is an optimal dual (all in the core); reported as an interval, main value alpha = 0.5 (the central split of
the interior-point solution: the analytic centre of the optimal dual face is symmetric in two identical rows). Same-proportion rule: annuity
(investment) and congestion rent of a line are split with the same alpha, i.e. its NET rent is split.

Owner codes used throughout: a country code ("VN"), a sorted pair for cross-border items ("KH|VN", first country gets alpha), "BUNKER", and
"SHARED" for right-hand sides / assets that belong to no player (reported separately, never folded into a player silently). Supplement 01 D3:
the ASEAN pool surplus (ownerless pool components, no right-hand side) stays a separate residual; a future total cap on extra-ASEAN imports
(any right-hand side without an owner) must be attributed BEFORE the run, else the audit flags the Owen premise as failed.

    PYTHONHASHSEED=0 python scripts_project/m12_allocation.py run --repo . --solved <dir>/<scenario>_solved.nc --scenario integrated --out <dir>
            [--solve-dir <dir>] [--label L] [--alpha 0.5]
    python scripts_project/m12_allocation.py benefit --integrated <dir> --disconnected <dir> --out <dir> [--repo .]
    python scripts_project/m12_allocation.py loo --full <dir> --loo VN=<dir> [--loo TH=<dir> ...] --out <dir> [--reference <json>]
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

SCRIPT = "scripts_project/m12_allocation.py"
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
BUNKER = "BUNKER"
SHARED = "SHARED"
PLAYERS = COUNTRIES + (BUNKER,)
B16_TOL = 1e-6                      # GATES_V6 G1c / B16: ledger identity relative error
ALPHA_MAIN = 0.5
ALPHA_GRID = (0.0, 0.5, 1.0)


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ----------------------------------------------------------------------------------------------------------------------------- owner codes / alpha
def pair(a: str, b: str) -> str:
    """owner code of an item between a and b: the country itself when equal, else the sorted pair "A|B"."""
    return a if a == b else "|".join(sorted((a, b)))


def shares(owner: str, alpha=ALPHA_MAIN) -> dict:
    """player shares of an owner code; alpha = share of the FIRST country of a sorted pair (scalar, or dict pair -> alpha)."""
    if "|" in owner:
        a, b = owner.split("|")
        al = float(alpha.get(owner, ALPHA_MAIN) if isinstance(alpha, dict) else alpha)
        return {a: al, b: 1.0 - al}
    return {owner: 1.0}


def fold(raw: dict, alpha=ALPHA_MAIN, players=PLAYERS) -> dict:
    """fold amounts by owner code into players (+ SHARED for anything that is not a player or a pair of players)."""
    out = {p: 0.0 for p in players}
    out[SHARED] = 0.0
    for k, v in raw.items():
        for p, s in shares(str(k), alpha).items():
            out[p if p in out and p != SHARED else SHARED] += s * float(v)
    return out


def alpha_interval(raw_excl_pairs: dict, pair_amounts: dict, players=PLAYERS) -> dict:
    """per-player range of the allocation over independent alpha_l in [0, 1] for every pair item.

    pair_amounts: {"A|B": amount added to the players' allocations (cost - value = - net rent)}. Player p's allocation is
    base_p + sum_l s_{l,p} amount_l with s in [0, 1]; the extremes of different players are not reached at the same alphas."""
    base = fold(raw_excl_pairs, ALPHA_MAIN, players)
    lo = dict(base); hi = dict(base)
    for k, v in pair_amounts.items():
        for p in str(k).split("|"):
            if p in lo:
                lo[p] += min(float(v), 0.0); hi[p] += max(float(v), 0.0)
    return {p: dict(min=lo[p], max=hi[p], width=hi[p] - lo[p]) for p in players}


# ----------------------------------------------------------------------------------------------------------------------------- dual form y' b
def dual_form(lo, hi, pi, owners, col_lo=None, col_hi=None, rc=None, col_owners=None) -> dict:
    """Owen dual form: sum of multiplier x active bound by owner code (EUR, objective units).

    Rows l <= a x <= u with multiplier pi (min problem: pi > 0 on the lower side, pi < 0 on the upper side; equality rows either). The
    active bound is l for pi > 0 and u for pi < 0; a multiplier on an infinite side (dual sign error of an interior point) contributes 0 and
    is reported as sign_error. Column bounds the same with the reduced costs rc. Returns dict(rows=..., columns=..., sign_error=...)."""
    def part(lo_, hi_, mu, own):
        lo_ = np.asarray(lo_, float); hi_ = np.asarray(hi_, float); mu = np.asarray(mu, float); own = np.asarray(own, dtype=object)
        b = np.where(mu > 0, lo_, np.where(mu < 0, hi_, 0.0))
        bad = ~np.isfinite(b)
        term = np.where(bad, 0.0, mu * np.where(bad, 0.0, b))
        s = pd.Series(term).groupby(own).sum()
        err = pd.Series(np.where(bad, np.abs(mu), 0.0)).groupby(own).sum()
        return {str(k): float(v) for k, v in s.items() if v != 0.0}, {str(k): float(v) for k, v in err.items() if v != 0.0}
    rows, err_r = part(lo, hi, pi, owners)
    cols, err_c = ({}, {}) if rc is None else part(col_lo, col_hi, rc, col_owners)
    tot = dict(rows)
    for k, v in cols.items():
        tot[k] = tot.get(k, 0.0) + v
    return dict(rows=rows, columns=cols, total=tot, sign_error_rows=err_r, sign_error_columns=err_c)


# ----------------------------------------------------------------------------------------------------------------------------- market-settlement form
def settle(assets: pd.DataFrame, alpha=ALPHA_MAIN, players=PLAYERS) -> dict:
    """market-settlement form from an asset table (one row per asset / load / constant).

    Columns: owner (code), cost (EUR, objective units incl. constants), value (EUR: sum over its buses and snapshots of
    nodal dual x injection; loads negative), value_own (part of value at buses of the same owner), value_foreign (rest).
    Allocation of an owner code = cost - value; pairs folded with alpha (same alpha for annuity and rent)."""
    net = (assets["cost"] - assets["value"]).groupby(assets["owner"].astype(str)).sum()
    raw = {str(k): float(v) for k, v in net.items()}
    alloc = fold(raw, alpha, players)
    pairs = {k: v for k, v in raw.items() if "|" in k}
    single = {k: v for k, v in raw.items() if "|" not in k}
    return dict(raw_by_owner=raw, allocation=alloc, pairs=pairs, interval=alpha_interval(single, pairs, players))


# ----------------------------------------------------------------------------------------------------------------------------- game checks
def coalitions(players) -> list:
    ps = list(players)
    return [frozenset(c) for r in range(1, len(ps) + 1) for c in itertools.combinations(ps, r)]


def core_violations(alloc: dict, cost: dict, tol: float = 0.0) -> list:
    """coalitions S whose allocation exceeds their own cost: sum_{i in S} phi_i - c(S) > tol (cost game core: phi(S) <= c(S))."""
    out = []
    for S, cS in cost.items():
        ex = sum(alloc[i] for i in S) - cS
        if ex > tol:
            out.append(dict(coalition=sorted(S), excess=float(ex)))
    return out


def loo_check(alloc: dict, c_full: float, c_loo: dict, tol: dict) -> dict:
    """leave-one-out: c'(i) = c(N) - c(N - i); core implies phi_i >= c'(i). tol = per-country threshold (bn or EUR, same unit)."""
    rows = {}
    for i, cNi in sorted(c_loo.items()):
        cp = c_full - cNi
        rows[i] = dict(c_N_minus_i=float(cNi), marginal_cost=float(cp), allocation=float(alloc[i]), margin=float(alloc[i] - cp),
                       tolerance=float(tol.get(i, 0.0)), passed=bool(alloc[i] - cp >= -float(tol.get(i, 0.0))))
    sum_marg = float(sum(v["marginal_cost"] for v in rows.values()))
    return dict(countries=rows, sum_marginal_costs=sum_marg, indivisible_cost=float(c_full - sum_marg),
                indivisible_cost_sign=("positive" if c_full - sum_marg > 0 else "negative" if c_full - sum_marg < 0 else "zero"),
                all_passed=bool(all(v["passed"] for v in rows.values())))


def scrb(c_full: float, standalone: dict, marginal: dict) -> dict:
    """separable costs - remaining benefits: phi_i = c'(i) + (c(i) - c'(i)) / sum_j (c(j) - c'(j)) x (c(N) - sum_j c'(j)); remaining
    benefits clipped at 0 (standard SCRB)."""
    nonsep = c_full - sum(marginal.values())
    rb = {i: max(standalone[i] - marginal[i], 0.0) for i in marginal}
    tot = sum(rb.values())
    return {i: float(marginal[i] + (rb[i] / tot * nonsep if tot > 0 else nonsep / len(marginal))) for i in marginal}


def proportional(total: float, weights: dict) -> dict:
    w = {k: float(v) for k, v in weights.items()}
    s = sum(w.values())
    return {k: total * v / s for k, v in w.items()}


# ----------------------------------------------------------------------------------------------------------------------------- solved network
DIRECT = ("capex_new", "fom_existing", "variable_cost", "co2_ship_freight", "co2_transit_freight", "co2_transit_ship_freight", "co2_transit_rail_freight")
XB_SUBJECTS = ("xb_share_infrastructure_cost", "xb_share_congestion_rent")
BASE_ELEC = ("electricity",)
FIXED_ELEC = ("electricity", "industry electricity", "land transport EV", "agriculture machinery electric")   # S4R R1 model_fixed_elec_total_twh


def entity_code(e: str) -> str:
    """s4d_ledger entity -> owner code: ASEAN_BUNKER -> BUNKER (12th player), ASEAN_POOL -> SHARED (no owner), XB:A|B@... -> A|B."""
    from s4d_ledger import BUNKER as LB, POOL
    e = str(e)
    if e == LB:
        return BUNKER
    if e == POOL:
        return SHARED
    return e[3:].split("@")[0] if e.startswith("XB:") else e


def corridor_components(n, length_shares: pd.DataFrame | None = None) -> pd.DataFrame:
    """one row per cross-border Line / Link (border_class cross_border): direct costs and settlement at both ends' duals, with the same rules and
    formulas as s4d_ledger.country_cost_ledger (owners, capex of new capacity, existing FOM incl. the meta ledger, marginal cost x flow x weight;
    settlement = payments for withdrawals - receipts for injections). net = costs + settlement = -(rent - annuity) = - net rent."""
    from s4d_ledger import FLOW, NOM, _ports, bus_entities, owners
    w = n.snapshot_weightings.objective; ent = bus_entities(n); own = owners(n, ent); price = n.buses_t.marginal_price
    sh = {}
    if length_shares is not None and len(length_shares):
        for _, r in length_shares.iterrows():
            sh[f"{r.component_type}:{r.component}"] = {str(r.country_a): float(r.share_a), str(r.country_b): float(r.share_b)}
    xbf = pd.DataFrame(n.meta.get("existing_cross_border_fom_ledger", []))
    rows = []
    for t in ("Line", "Link"):
        d = n.df(t)
        sel = [x for x in d.index if str(own[t].get(x, "")).startswith("XB:")]
        if not sel:
            continue
        nom = NOM[t]; dd = d.loc[sel]
        capex = ((dd[nom + "_opt"] - dd[nom]) * dd.capital_cost).where(dd[nom + "_extendable"], 0.0)
        fom = pd.to_numeric(dd.existing_annual_fixed_om_eur, errors="coerce").fillna(0.0) if "existing_annual_fixed_om_eur" in dd else pd.Series(0.0, index=sel)
        if len(xbf):
            extra = xbf[xbf.component_type == t].groupby("component").annual_fom_eur.sum()
            fom = fom.add(extra.reindex(sel).fillna(0.0), fill_value=0.0)
        var = pd.Series(0.0, index=sel)
        if t in FLOW:
            mc = n.get_switchable_as_dense(t, "marginal_cost").reindex(columns=sel, fill_value=0.0)
            var = (n.pnl(t)[FLOW[t]].reindex(columns=sel, fill_value=0.0) * mc).mul(w, axis=0).sum()
        settle_ = pd.Series(0.0, index=sel)
        for p in _ports(d):
            pn = n.pnl(t).get("p" + p[3:])
            if pn is None:
                continue
            ok = [x for x in sel if isinstance(d.at[x, p], str) and d.at[x, p]]
            if not ok:
                continue
            lam = price[[d.at[x, p] for x in ok]].to_numpy()
            settle_ = settle_.add(pd.Series((pn.reindex(columns=ok, fill_value=0.0).to_numpy() * lam * w.to_numpy()[:, None]).sum(axis=0), index=ok), fill_value=0.0)
        p0 = n.pnl(t)["p0"].reindex(columns=sel, fill_value=0.0)
        e01 = p0.clip(lower=0).mul(w, axis=0).sum(); e10 = (-p0).clip(lower=0).mul(w, axis=0).sum()
        for x in sel:
            pr = entity_code(own[t][x]); a, b = pr.split("|")
            c0 = str(ent[d.at[x, "bus0"]]); s = sh.get(f"{t}:{x}") or (sh.get(f"{t}:{x[: -len('-reversed')]}") if x.endswith("-reversed") else None)
            rows.append(dict(component_type=t, component=x, pair=pr, carrier=str(d.at[x, "carrier"]), country_bus0=c0,
                             capacity_initial=float(d.at[x, nom]), capacity_opt=float(d.at[x, nom + "_opt"]), capex_new=float(capex[x]), fom_existing=float(fom[x]),
                             variable_cost=float(var[x]), settlement=float(settle_[x]),
                             energy_a_to_b_mwh=float(e01[x] if c0 == a else e10[x]), energy_b_to_a_mwh=float(e10[x] if c0 == a else e01[x]),
                             length_share_a=(float(s[a]) if s and set(s) == {a, b} else np.nan)))
    C = pd.DataFrame(rows)
    if len(C):
        C["costs"] = C.capex_new + C.fom_existing + C.variable_cost
        C["net"] = C.costs + C.settlement
        C["rent"] = -C.settlement
        C["net_rent"] = -C.net
    return C


def load_energy_twh(n) -> dict:
    """annual load energy by owner country and load carrier (TWh): owner = Load.country when it is a country, else the bus country."""
    from s4d_ledger import bus_entities
    d = n.loads; ent = bus_entities(n)
    c = d.country.astype(str) if "country" in d else pd.Series("", index=d.index)
    own = c.where(c.isin(list(COUNTRIES)), d.bus.map(ent).astype(str)).map(entity_code)
    e = n.get_switchable_as_dense("Load", "p_set").mul(n.snapshot_weightings.objective, axis=0).sum() / 1e6
    df = pd.DataFrame(dict(owner=own, carrier=d.carrier.astype(str), twh=e.reindex(d.index).fillna(0.0)))
    out = {}
    for (o, car), v in df.groupby(["owner", "carrier"]).twh.sum().items():
        out.setdefault(o, {})[car] = float(v)
    return out


def allocation_from_network(n, length_shares: pd.DataFrame | None = None) -> dict:
    """Owen allocation (market-settlement form) of a solved network: ledger of s4d_ledger (rules of decision 91a), corridors split with alpha."""
    from s4d_ledger import country_cost_ledger
    L, ident, diag = country_cost_ledger(n, length_shares=length_shares)
    C = corridor_components(n, length_shares)
    L = L.assign(owner=L.entity.map(entity_code))
    noxb = L[~L.subject.isin(XB_SUBJECTS)]
    base = noxb.groupby("owner").eur.sum().to_dict()
    pairs = C.groupby("pair").net.sum().to_dict() if len(C) else {}
    # corridor totals must equal the ledger's corridor table (same formulas)
    dc = {entity_code(k): v for k, v in diag["corridors"].items()}
    corr_dev = max([abs(pairs.get(k, 0.0) - v["net"]) for k, v in dc.items()] + [abs(v) for k, v in pairs.items() if k not in dc] + [0.0])
    owners_ = sorted(set(base) | set(pairs))
    raw = {k: base.get(k, 0.0) + pairs.get(k, 0.0) for k in owners_}

    def alloc(alpha):
        return fold(raw, alpha)
    len_alpha = {}
    if len(C):
        for _, r in C.iterrows():
            len_alpha.setdefault(r.pair, []).append((r.length_share_a if np.isfinite(r.length_share_a) else 0.5, r.net))
    # length split: per component share (s4d_ledger: missing shares -> 0.5); fold component by component
    raw_len = {k: v for k, v in base.items()}
    for pr, lst in len_alpha.items():
        a, b = pr.split("|")
        for s, v in lst:
            raw_len[a] = raw_len.get(a, 0.0) + s * v; raw_len[b] = raw_len.get(b, 0.0) + (1 - s) * v
    by_alpha = {f"{a:g}": alloc(a) for a in ALPHA_GRID}
    main = by_alpha[f"{ALPHA_MAIN:g}"]
    led_tot = L.groupby("owner").eur.sum(); led_len = L.groupby("owner").eur_length_split.sum()
    ledger_dev = max(abs(main.get(k, 0.0) - float(v)) for k, v in led_tot.items() if k in main)
    length_alloc = fold({k: v for k, v in raw_len.items()}, ALPHA_MAIN)   # raw_len has no pairs left
    ledger_len_dev = max(abs(length_alloc.get(k, 0.0) - float(v)) for k, v in led_len.items() if k in length_alloc)
    single = {k: v for k, v in raw.items() if "|" not in k}
    inter = alpha_interval(single, pairs)
    obj = float(ident["objective"])
    players_sum = float(sum(main[p] for p in PLAYERS)) + float(base.get("OBJECTIVE_EXTRA", 0.0))
    # breakdown per player (EUR): asset costs (subjects of direct costs; extra-ASEAN imports = variable cost of import carriers), settlements
    # (net purchases - net sales at the duals, by subject), corridor share at alpha
    br = {}
    for p in list(PLAYERS) + [SHARED]:
        q = noxb[noxb.owner == p]
        dct = q[q.subject.isin(DIRECT)]; st = q[~q.subject.isin(DIRECT)]
        imp = dct[(dct.subject == "variable_cost") & dct.carrier.str.contains("import")]
        br[p] = dict(asset_cost=float(dct.eur.sum()), asset_cost_by_subject={k: float(v) for k, v in dct.groupby("subject").eur.sum().items()},
                     extra_asean_imports=float(imp.eur.sum()), net_purchases=float(st.eur.sum()),
                     net_purchases_by_subject={k: float(v) for k, v in st.groupby("subject").eur.sum().items()},
                     corridor_share_alpha_main=float(main[p] - dct.eur.sum() - st.eur.sum()))
    return dict(objective=obj, ledger_identity=ident, raw_by_owner=raw, pairs_net=pairs, by_alpha=by_alpha, length_split=length_alloc,
                interval=inter, breakdown=br, corridors=C, ledger=L,
                identity=dict(objective=obj, players_sum=players_sum, shared=float(main[SHARED]), difference=players_sum - obj,
                              relative_error=abs(players_sum - obj) / max(1.0, abs(obj)), relative_error_incl_shared=abs(players_sum + main[SHARED] - obj) / max(1.0, abs(obj)),
                              tolerance=B16_TOL, passed=bool(abs(players_sum - obj) / max(1.0, abs(obj)) <= B16_TOL),
                              note="B16: sum of the 11 countries + BUNKER = objective (incl. the fixed-once constants); the ASEAN pool surplus (SHARED) is the difference term"),
                checks=dict(corridor_table_max_abs_dev_eur=float(corr_dev), ledger_alpha_half_max_abs_dev_eur=float(ledger_dev),
                            ledger_length_split_max_abs_dev_eur=float(ledger_len_dev)))


def importer_of(C: pd.DataFrame) -> dict:
    """S4P aspect 8 rule: importer of a pair = net electricity (AC + DC) flow direction; pairs without an electricity corridor: all carriers."""
    out = {}
    for pr, g in C.groupby("pair"):
        a, b = pr.split("|")
        ge = g[g.carrier.isin(["AC", "DC"])]
        ge = ge if len(ge) else g
        ab, ba = float(ge.energy_a_to_b_mwh.sum()), float(ge.energy_b_to_a_mwh.sum())
        out[pr] = dict(importer=b if ab > ba else a, exporter=a if ab > ba else b, e_a_to_b_twh=ab / 1e6, e_b_to_a_twh=ba / 1e6)
    return out


def s4p_rules(res: dict) -> dict:
    """C1 item 7: S4P aspect-8 rules on this run vs the alpha family (same proportion). (i) = alpha 0.5; (ii) / (iii) move the corridor rent
    (settlement) to the importer / exporter and keep the infrastructure cost half / half; their same-proportion counterparts give the
    importer / exporter alpha = 1 for annuity AND rent; (v) in-country length = alpha_l = length share (same proportion, inside [0, 1])."""
    C = res["corridors"]
    if not len(C):
        return dict(applicable=False, note="no cross-border corridor in this run (disconnected): every settlement rule gives the same allocation")
    imp = importer_of(C)
    base = {k: v for k, v in res["raw_by_owner"].items() if "|" not in k}
    pc = C.groupby("pair")[["costs", "settlement", "net"]].sum()
    rules = {}
    for name, who in (("ii_rent_to_importer", "importer"), ("iii_rent_to_exporter", "exporter")):
        r = dict(base); sp = dict(base)
        for pr, v in pc.iterrows():
            a, b = pr.split("|"); w_ = imp[pr][who]
            for c in (a, b):
                r[c] = r.get(c, 0.0) + 0.5 * v.costs + (v.settlement if c == w_ else 0.0)
                sp[c] = sp.get(c, 0.0) + (v.net if c == w_ else 0.0)
        rules[name] = dict(s4p_rule=fold(r), same_proportion_counterpart=fold(sp))
    out = {}
    for p in COUNTRIES:
        row = dict(i_current_alpha_half=res["by_alpha"]["0.5"][p], v_length_split=res["length_split"][p])
        for name, v in rules.items():
            row[name] = v["s4p_rule"][p]; row[name + "_same_proportion"] = v["same_proportion_counterpart"][p]
            row[name + "_minus_same_proportion"] = v["s4p_rule"][p] - v["same_proportion_counterpart"][p]
        out[p] = row
    infra_half = {pr: 0.5 * float(v.costs) for pr, v in pc.iterrows()}
    return dict(applicable=True, importers=imp, by_country_eur=out, corridor_costs_half_eur=infra_half,
                conclusion=("S4P rules (ii) / (iii) split the corridor rent 100 / 0 but keep the infrastructure cost (annuity, existing FOM, operating cost) "
                            "50 / 50: NOT the same proportion. Their difference to the same-proportion rule (alpha = 1 for the importer / exporter) is "
                            "+/- half of each corridor's infrastructure cost for the two countries of the pair. Rule (i) (alpha 0.5) and rule (v) "
                            "(alpha = in-country length share, applied to costs and rent alike) are same-proportion and inside the Owen interval."))


# ----------------------------------------------------------------------------------------------------------------------------- inputs of the comparisons
SSP2_NAMES = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Laos": "LA", "Lao PDR": "LA", "Malaysia": "MY", "Myanmar": "MM", "Philippines": "PH",
              "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "Viet Nam": "VN", "Vietnam": "VN"}
TL_POP_2050_UN_WPP = 1.8892495   # million; registry download_un_wpp2024_tl_population_2050 (UN WPP 2024 medium variant, 1,889,249.5 persons)
TL_PEERS = ("KH", "LA", "MM")    # M08b TL rule (m08b_demand.py): TL outside AEO8 -> simple mean of the KH / LA / MM per-capita values
AEO8_D2_CSV = "research_inputs/demand_v5/sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv"   # M08b source of the industry growth (same bytes)
WEIGHTS_MAIN = ("population_aeo8_d1", "gdp_aeo8_d2", "electricity_fixed", "electricity_base")   # supplement 01 D5: same sources as the model
WEIGHTS_COMPARISON = ("population_ssp2", "gdp_ppp_ssp2")


def _num(v) -> float:
    return float(str(v).replace(",", "").strip())


def socio_weights(repo: Path) -> dict:
    """2050 population and GDP by country (supplement 01 D5: one main source per variable, the one the model uses).
    Main: population = AEO8 table D.1 2050 (TL: UN WPP 2024 median, the numbers of the demand anchoring, m08b_demand.py); GDP = AEO8 table D.2
    real GDP PPP 2017 in 2050 (the table behind the industry growth of m08b_demand.py), TL = mean of the KH / LA / MM GDP per capita (D.2 / D.1)
    x the TL population (the M08b TL rule for per-capita values). Comparison: SSP2 2050 (IIASA-WiC POP 2025, OECD ENV-Growth 2025 GDP|PPP)."""
    src = repo / "research_inputs/registry_v5/sources"
    s = pd.read_csv(src / "SSP2_2025_POP_GDP_ASEAN11.csv")
    s["c"] = s.region.map(SSP2_NAMES)
    pop = s[s.variable == "Population"].set_index("c")["2050"].astype(float).to_dict()
    gdp = s[s.variable == "GDP|PPP"].set_index("c")["2050"].astype(float).to_dict()
    a = pd.read_csv(src / "AEO8_2050_BY_COUNTRY.csv", dtype=str)
    a = a[(a.indicator == "Population") & (a.year == "2050") & (a.scenario == "all scenarios (constant)")]
    aeo = {SSP2_NAMES[r.country]: _num(r.value_as_printed) for r in a.itertuples() if r.country in SSP2_NAMES}
    aeo["TL"] = TL_POP_2050_UN_WPP
    d2 = pd.read_csv(repo / AEO8_D2_CSV, dtype=str)
    g = {SSP2_NAMES[r.country]: _num(r.y2050) for r in d2.itertuples() if r.country in SSP2_NAMES}
    g["TL"] = float(np.mean([g[p] / aeo[p] for p in TL_PEERS])) * aeo["TL"]
    return dict(population_aeo8_d1_m=aeo, gdp_aeo8_d2_musd2017ppp=g, population_ssp2_m=pop, gdp_ppp_ssp2_bn_usd2017=gdp,
                sources=dict(population_aeo8=f"{src.name}/AEO8_2050_BY_COUNTRY.csv table D.1 2050 (all scenarios); TL UN WPP 2024 median 1,889,249.5 (as m08b_demand.py)",
                             gdp_aeo8=f"{AEO8_D2_CSV} table D.2 real GDP PPP 2017 (million USD) 2050; TL = mean({', '.join(TL_PEERS)}) GDP per capita x TL population (M08b TL rule)",
                             population_ssp2=f"{src.name}/SSP2_2025_POP_GDP_ASEAN11.csv IIASA-WiC POP 2025 SSP2 2050 (comparison)",
                             gdp_ssp2=f"{src.name}/SSP2_2025_POP_GDP_ASEAN11.csv OECD ENV-Growth 2025 SSP2 GDP|PPP 2050 (billion USD2017; comparison)"),
                d2_sha256=sha(repo / AEO8_D2_CSV))


def thresholds_bn(solve_dir: Path | None, reference: Path | None) -> tuple[dict, str]:
    """per-country tolerance of C1 (b) (decision 119): from the run's PRECISION.json (after any regrade) or a reference JSON."""
    from s4o_c1_precision import L23_REFERENCE, threshold_bn
    if reference is not None:
        ref = json.loads(Path(reference).read_text())
        return {c: threshold_bn(c, ref) for c in COUNTRIES}, f"reference {reference}: {ref.get('source', '')[:120]}"
    if solve_dir is not None and (Path(solve_dir) / "PRECISION.json").exists():
        P = json.loads((Path(solve_dir) / "PRECISION.json").read_text())
        cc = (P.get("b_primal_violations") or {}).get("country_check") or {}
        if cc and all("threshold_bn" in cc.get(c, {}) for c in COUNTRIES):
            return {c: float(cc[c]["threshold_bn"]) for c in COUNTRIES}, f"PRECISION.json of {solve_dir} ({((P.get('reference') or {}).get('source') or P.get('l23_reference_note') or '')[:120]})"
    return {c: threshold_bn(c, L23_REFERENCE) for c in COUNTRIES}, "L23 default reference (s4o_c1_precision.L23_REFERENCE)"


def precision_context(solve_dir: Path | None, precision: Path | None = None) -> dict:
    p = Path(precision) if precision is not None else (Path(solve_dir) / "PRECISION.json" if solve_dir is not None else None)
    if p is None or not p.exists():
        return dict(available=False, note="no PRECISION.json: the price-settled allocation is provisional (decision 119 (c) not shown)")
    P = json.loads(p.read_text())
    g = P.get("grade") or {}
    return dict(available=True, file=str(p), grade=g.get("grade"), c_passed=g.get("c"), price_settled_results=g.get("price_settled_results"),
                accepted=(P.get("acceptance") or {}).get("accepted"), termination=P.get("termination"),
                note="Owen allocation uses the duals: usable only when C1 (c) passed (registry run_rule_formal_2920: ACCEPTED_LAYER2 for formal runs)")


# ----------------------------------------------------------------------------------------------------------------------------- run / outputs
def update_exports(d: Path, names) -> dict:
    p = d / "EXPORTS.json"
    ex = json.loads(p.read_text()) if p.exists() else {}
    for f in names:
        if (d / f).exists():
            ex[f] = dict(bytes=(d / f).stat().st_size, sha256=sha(d / f), source="m12_allocation.py (M12 C1, item 133)")
    p.write_text(json.dumps(ex, indent=1))
    return ex


def _fx() -> dict:
    from s4d_ledger import report_currency
    return report_currency(None)


def run(solved: Path, scenario: str, out: Path, solve_dir: Path | None, label: str, repo: Path, register: bool, precision: Path | None = None) -> dict:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=True)
    rec = json.loads((solve_dir / "SOLVE_RECEIPT.json").read_text()) if solve_dir and (solve_dir / "SOLVE_RECEIPT.json").exists() else {}
    fx = _fx()
    meta = dict(script=SCRIPT, scenario=scenario, label=label, solved_network=str(solved), solve_dir=str(solve_dir) if solve_dir else None,
                termination=rec.get("termination_condition"), receipt_objective=rec.get("objective"), report_currency=fx,
                alpha_definition="alpha = share of the FIRST country (alphabetical) of a cross-border pair, applied to the corridor's annuity, existing FOM, "
                                 "operating cost AND rent alike (same-proportion rule); main value 0.5 (central split of the interior-point solution)",
                precision=precision_context(solve_dir, precision), solver_runs=0)
    if solved is None or not Path(solved).exists():
        res = dict(meta, computable=False, missing=str(solved))
        (out / "ALLOCATION.json").write_text(json.dumps(res, indent=1, default=str))
        (out / "ALLOCATION.md").write_text(f"# ALLOCATION（M12 C1）\n\n无法计算：缺少求解后网络 `{solved}`。\n")
        if register:
            update_exports(out, ("ALLOCATION.json", "ALLOCATION.md"))
        return res
    import pypsa
    from s4d_ledger import load_length_shares
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(solved))
    meta["solved_network_sha256"] = sha(Path(solved))
    A = allocation_from_network(n, load_length_shares())
    C = A.pop("corridors"); A.pop("ledger")
    rules = s4p_rules(dict(A, corridors=C))
    loads = load_energy_twh(n)
    has_bunker = bool(abs(A["by_alpha"]["0.5"][BUNKER]) > 0 or BUNKER in loads)
    tab = []
    for p in PLAYERS:
        b = A["breakdown"][p]; r = dict(player=p)
        r.update({f"alloc_alpha_{k}_eur": v[p] for k, v in A["by_alpha"].items()})
        r.update(alloc_length_split_eur=A["length_split"][p], interval_min_eur=A["interval"][p]["min"], interval_max_eur=A["interval"][p]["max"],
                 asset_cost_eur=b["asset_cost"], extra_asean_imports_eur=b["extra_asean_imports"], net_purchases_eur=b["net_purchases"],
                 corridor_share_alpha_half_eur=b["corridor_share_alpha_main"])
        r["alloc_alpha_0.5_usd2020"] = r["alloc_alpha_0.5_eur"] * fx["fx_per_eur2020"]
        r["interval_min_usd2020"] = r["interval_min_eur"] * fx["fx_per_eur2020"]; r["interval_max_usd2020"] = r["interval_max_eur"] * fx["fx_per_eur2020"]
        if rules.get("applicable") and p in rules["by_country_eur"]:
            r.update({f"s4p_{k}_eur": v for k, v in rules["by_country_eur"][p].items() if k not in ("i_current_alpha_half", "v_length_split")})
        tab.append(r)
    T = pd.DataFrame(tab).set_index("player")
    T.loc[SHARED] = np.nan
    T.loc[SHARED, ["alloc_alpha_0.5_eur", "asset_cost_eur", "net_purchases_eur"]] = [A["by_alpha"]["0.5"][SHARED], A["breakdown"][SHARED]["asset_cost"], A["breakdown"][SHARED]["net_purchases"]]
    T.to_csv(out / "ALLOCATION.csv")
    if len(C):
        C.to_csv(out / "ALLOCATION_LINES.csv", index=False)
    res = dict(meta, computable=True, objective=A["objective"], identity=A["identity"], checks=A["checks"], bunker_player_present=has_bunker,
               allocation_eur={k: v for k, v in A["by_alpha"].items()}, length_split_eur=A["length_split"], interval_eur=A["interval"],
               allocation_usd2020_alpha_half={p: A["by_alpha"]["0.5"][p] * fx["fx_per_eur2020"] for p in list(PLAYERS) + [SHARED]},
               breakdown_eur=A["breakdown"], raw_by_owner_eur=A["raw_by_owner"], corridor_pairs=_pairs_summary(C), s4p_rules=rules, load_energy_twh=loads,
               ledger_identity=A["ledger_identity"], seconds=time.time() - t0)
    (out / "ALLOCATION.json").write_text(json.dumps(res, indent=1, default=str))
    (out / "ALLOCATION.md").write_text(markdown_run(res))
    if register:
        update_exports(out, ("ALLOCATION.json", "ALLOCATION.csv", "ALLOCATION.md", "ALLOCATION_LINES.csv"))
    return res


def _pairs_summary(C: pd.DataFrame) -> dict:
    if not len(C):
        return {}
    g = C.groupby("pair")
    out = {}
    for pr, q in g:
        a, b = pr.split("|")
        nr = float(q.net_rent.sum())
        out[pr] = dict(components=int(len(q)), costs_eur=float(q.costs.sum()), rent_eur=float(q.rent.sum()), net_rent_eur=nr,
                       energy_a_to_b_twh=float(q.energy_a_to_b_mwh.sum() / 1e6), energy_b_to_a_twh=float(q.energy_b_to_a_mwh.sum() / 1e6),
                       allocation_change_first_country_eur={f"{al:g}": -al * nr for al in ALPHA_GRID},
                       allocation_change_second_country_eur={f"{al:g}": -(1 - al) * nr for al in ALPHA_GRID}, first_country=a, second_country=b)
    return out


def bn(x) -> str:
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x / 1e9:,.3f}"


def markdown_run(r: dict) -> str:
    al = r["allocation_eur"]; it = r["interval_eur"]; fx = r["report_currency"]["fx_per_eur2020"]
    pc = r["precision"]
    L = [f"# ALLOCATION（M12 C1，Owen 分摊；只读，未求解）", "",
         f"- 运行：`{r['solve_dir'] or r['solved_network']}`（{r['scenario']}，{r['label']}）；终止 `{r.get('termination')}`；目标值 {r['objective']:,.0f} EUR2020。",
         f"- 精度（C1 / 第 119 项）：" + (f"等级 {pc.get('grade')}，(c) {pc.get('c_passed')}，节点电价结算 {pc.get('price_settled_results')}" if pc.get("available") else pc["note"]),
         f"- 恒等式（B16）：11 国 + 燃料舱 = {r['identity']['players_sum']:,.0f}，目标值 {r['identity']['objective']:,.0f}，相对误差 {r['identity']['relative_error']:.2e}"
         f"（≤ 1e-6：**{r['identity']['passed']}**）；共享（东盟池盈余，无所有者）{r['identity']['shared']:,.0f} EUR。",
         f"- 对账：α = 0.5 与现行账本 COUNTRY_COST_LEDGER 最大偏差 {r['checks']['ledger_alpha_half_max_abs_dev_eur']:.3g} EUR；按长度分摊偏差 {r['checks']['ledger_length_split_max_abs_dev_eur']:.3g} EUR；"
         f"走廊逐组件合计与账本走廊表偏差 {r['checks']['corridor_table_max_abs_dev_eur']:.3g} EUR。",
         f"- 燃料舱参与者：{'有' if r['bunker_player_present'] else '**该网络没有燃料舱参与者**'}。",
         f"- α 定义：{r['alpha_definition']}。汇率 1 EUR2020 = {fx:.6f} USD2020（1 / {r['report_currency']['input_eur_per_usd']:.9f}）。", "",
         "## 12 个参与者的分摊（bn）", "",
         "| 参与者 | 资产成本 EUR | 其中区域外进口 | 净买入 − 净卖出 | 走廊份额（α 0.5） | **分摊 α 0.5 EUR** | 分摊 USD2020 | α 0 | α 1 | 按长度 | 区间下限 | 区间上限 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for p in list(PLAYERS) + [SHARED]:
        b = r["breakdown_eur"][p]
        L.append(f"| {p} | {bn(b['asset_cost'])} | {bn(b['extra_asean_imports'])} | {bn(b['net_purchases'])} | {bn(b['corridor_share_alpha_main'])} | **{bn(al['0.5'][p])}** | "
                 f"{bn(al['0.5'][p] * fx)} | {bn(al['0'][p])} | {bn(al['1'][p])} | {bn(r['length_split_eur'].get(p))} | {bn(it[p]['min']) if p in it else '—'} | {bn(it[p]['max']) if p in it else '—'} |")
    L += ["", "区间：每条跨境线的 α 各自在 [0, 1] 内取值时该参与者分摊的范围；各国的端点不能同时达到。", ""]
    if r["corridor_pairs"]:
        L += ["## 跨境线路净租金（按国家对；逐线明细见 ALLOCATION_LINES.csv）", "",
              "| 国家对 | 组件数 | 年化投资 + FOM + 运行 bn | 租金 bn | 净租金 bn | a→b TWh | b→a TWh | 第一国分摊变化 α 0 / 0.5 / 1 | 第二国 α 0 / 0.5 / 1 |", "|---|---|---|---|---|---|---|---|---|"]
        for pr, v in r["corridor_pairs"].items():
            a1 = v["allocation_change_first_country_eur"]; a2 = v["allocation_change_second_country_eur"]
            L.append(f"| {pr} | {v['components']} | {bn(v['costs_eur'])} | {bn(v['rent_eur'])} | {bn(v['net_rent_eur'])} | {v['energy_a_to_b_twh']:.2f} | {v['energy_b_to_a_twh']:.2f} | "
                     f"{bn(a1['0'])} / {bn(a1['0.5'])} / {bn(a1['1'])} | {bn(a2['0'])} / {bn(a2['0.5'])} / {bn(a2['1'])} |")
        L.append("")
    s = r["s4p_rules"]
    L += ["## 与 S4P 结算规则对照（C1 第 7 项）", ""]
    if s.get("applicable"):
        L += [s["conclusion"], "", "| 国 | (i) α 0.5 | (ii) 租归进口方 | (ii) 同比例 | (ii) − 同比例 | (iii) 租归出口方 | (iii) 同比例 | (iii) − 同比例 | (v) 按长度 |", "|---|---|---|---|---|---|---|---|---|"]
        for p, v in s["by_country_eur"].items():
            L.append(f"| {p} | {bn(v['i_current_alpha_half'])} | {bn(v['ii_rent_to_importer'])} | {bn(v['ii_rent_to_importer_same_proportion'])} | {bn(v['ii_rent_to_importer_minus_same_proportion'])} | "
                     f"{bn(v['iii_rent_to_exporter'])} | {bn(v['iii_rent_to_exporter_same_proportion'])} | {bn(v['iii_rent_to_exporter_minus_same_proportion'])} | {bn(v['v_length_split'])} |")
    else:
        L.append(s["note"])
    L += ["", f"用时 {r.get('seconds', 0):.0f} s；未调用求解器。"]
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------------------------------------------------------------- benefit / proportional rules
def _alloc_json(d: Path) -> dict:
    p = Path(d) / "ALLOCATION.json"
    r = json.loads(p.read_text())
    if not r.get("computable"):
        raise ValueError(f"{p} is not computable: {r.get('missing')}")
    return r


def _elec(le: dict, carriers) -> dict:
    return {c: float(sum((le.get(c) or {}).get(k, 0.0) for k in carriers)) for c in COUNTRIES}


def _dual_alloc(run_dir: Path, override: Path | None) -> dict | None:
    """Owen dual form (m12_rhs_audit.py: y'b + constants) of a run when available: <run>/m12_owen/OWEN.json (main-value file, supplement 01 D1),
    else <run>/m12_owen/RHS_AUDIT.json (dual_form block), or an explicit file of either kind. Returns allocation (alpha 0.5), interval, source."""
    cands = [Path(override)] if override is not None else [Path(run_dir) / "m12_owen" / "OWEN.json", Path(run_dir) / "m12_owen" / "RHS_AUDIT.json"]
    for p in cands:
        if not p.exists():
            continue
        r = json.loads(p.read_text())
        if r.get("main_form") == "owen_dual_form":
            return dict(allocation=r["allocation_eur"]["0.5"], interval=r["interval_eur"], source=str(p), usable=r.get("usable_for_allocation"),
                        identity_passed=(r.get("identity") or {}).get("passed"), premise_passed=(r.get("premise") or {}).get("passed"))
        d = r.get("dual_form") or {}
        if d.get("allocation_alpha_half"):
            return dict(allocation=d["allocation_alpha_half"], interval=d.get("interval"), source=str(p), usable=None, identity_passed=None, premise_passed=None)
    return None


def _loo_marginals(loo_check: Path | None) -> tuple[dict, str | None]:
    """c'(i) of the countries with a leave-one-out run, from LOO_CHECK.json (the D8-adjusted value when present)."""
    if loo_check is None or not Path(loo_check).exists():
        return {}, None
    r = json.loads(Path(loo_check).read_text())
    if r.get("computable") is False:
        return {}, f"{loo_check} (not computable: {str(r.get('reason', ''))[:80]})"
    cs = (r.get("check") or {}).get("countries") or {}
    return ({c: dict(c_prime=float(v.get("marginal_cost_adjusted", v["marginal_cost"])), adjusted="marginal_cost_adjusted" in v) for c, v in cs.items()},
            str(loo_check))


def benefit(int_dir: Path, dis_dir: Path, out: Path, repo: Path, int_dual: Path | None = None, dis_dual: Path | None = None, loo_check: Path | None = None) -> dict:
    """C1 items 4 / 5: benefit = disconnected allocation - integrated allocation (alpha 0.5 and the alpha interval); proportional rules splitting
    B6 = objective(disconnected) - objective(integrated) among the 11 countries (the bunker pays its disconnected allocation, benefit 0).
    Main value (supplement 01 D1): the Owen dual form y'b of both runs (m12_owen/OWEN.json); the market-settlement form (ALLOCATION.json, the
    current ledger) is reported alongside. Without the dual forms of both runs the market form is the main value (flagged)."""
    out.mkdir(parents=True, exist_ok=True)
    I, D = _alloc_json(int_dir), _alloc_json(dis_dir)
    I["precision"] = precision_context(int_dir, None) if (Path(int_dir) / "PRECISION.json").exists() else I.get("precision")   # after any regrade
    D["precision"] = precision_context(dis_dir, None) if (Path(dis_dir) / "PRECISION.json").exists() else D.get("precision")
    dI, dD = _dual_alloc(int_dir, int_dual), _dual_alloc(dis_dir, dis_dual)
    fx = I["report_currency"]["fx_per_eur2020"]
    mI, mD = I["allocation_eur"]["0.5"], D["allocation_eur"]["0.5"]
    mben = {p: mD[p] - mI[p] for p in PLAYERS}
    mrng = {p: dict(min=D["interval_eur"][p]["min"] - I["interval_eur"][p]["max"], max=D["interval_eur"][p]["max"] - I["interval_eur"][p]["min"]) for p in PLAYERS}
    dual = dI is not None and dD is not None
    if dual:
        pI, pD = dI["allocation"], dD["allocation"]
        iI, iD = dI.get("interval") or I["interval_eur"], dD.get("interval") or D["interval_eur"]
    else:
        pI, pD, iI, iD = mI, mD, I["interval_eur"], D["interval_eur"]
    main_form = "owen_dual_form" if dual else "market_settlement_form (dual form of both runs not available)"
    ben = {p: pD[p] - pI[p] for p in PLAYERS}
    rng = {p: dict(min=iD[p]["min"] - iI[p]["max"], max=iD[p]["max"] - iI[p]["min"]) for p in PLAYERS}
    b6 = float(D["objective"] - I["objective"])
    sw = socio_weights(repo)
    le = I.get("load_energy_twh") or {}
    w = dict(population_aeo8_d1=sw["population_aeo8_d1_m"], gdp_aeo8_d2=sw["gdp_aeo8_d2_musd2017ppp"], electricity_fixed=_elec(le, FIXED_ELEC),
             electricity_base=_elec(le, BASE_ELEC), population_ssp2=sw["population_ssp2_m"], gdp_ppp_ssp2=sw["gdp_ppp_ssp2_bn_usd2017"])
    assert tuple(w) == WEIGHTS_MAIN + WEIGHTS_COMPARISON
    tol_bn, tol_src = thresholds_bn(Path(int_dir), None)
    tol = {c: tol_bn[c] * 1e9 for c in COUNTRIES}
    lc, lc_src = _loo_marginals(loo_check)
    total_b = float(I["objective"] - pI[BUNKER] - pI.get(SHARED, 0.0))   # (B): the 11 countries share c(N) - bunker - pool residual
    owen_chk = dict(loo={c: dict(payment_eur=pI[c], marginal_cost_eur=v["c_prime"], margin_eur=pI[c] - v["c_prime"], passed=bool(pI[c] - v["c_prime"] >= -tol[c]))
                         for c, v in lc.items()},
                    ir={c: dict(payment_eur=pI[c], disconnected_eur=pD[c], margin_eur=pD[c] - pI[c], passed=bool(pI[c] <= pD[c] + tol[c])) for c in COUNTRIES})
    rules = {}
    for k, wt in w.items():
        s = {c: float(wt.get(c, 0.0)) for c in COUNTRIES}
        share = proportional(b6, s)
        pay = {c: pD[c] - share[c] for c in COUNTRIES}
        la = {c: dict(benefit_eur=share[c], max_benefit_eur=pD[c] - v["c_prime"], payment_eur=pay[c], marginal_cost_eur=v["c_prime"], margin_eur=pay[c] - v["c_prime"],
                      tolerance_eur=tol[c], passed=bool(pay[c] - v["c_prime"] >= -tol[c])) for c, v in lc.items()}
        pb = proportional(total_b, s)
        ir = {c: dict(payment_eur=pb[c], disconnected_eur=pD[c], benefit_eur=pD[c] - pb[c], tolerance_eur=tol[c], passed=bool(pb[c] <= pD[c] + tol[c])) for c in COUNTRIES}
        rules[k] = dict(weights=s,
                        A_split_b6=dict(benefit_eur=share, payment_eur=pay, minus_owen_payment_eur={c: pay[c] - pI[c] for c in COUNTRIES},
                                        negative_benefit=[c for c in COUNTRIES if share[c] < 0],
                                        owen_sign_differs=[c for c in COUNTRIES if ben[c] != 0 and np.sign(share[c]) != np.sign(ben[c])],
                                        loo_check=la, loo_violations=[c for c, v in la.items() if not v["passed"]]),
                        B_split_total=dict(total_eur=total_b, payment_eur=pb, benefit_eur={c: pD[c] - pb[c] for c in COUNTRIES},
                                           minus_owen_payment_eur={c: pb[c] - pI[c] for c in COUNTRIES}, ir_check=ir,
                                           ir_violations=[c for c, v in ir.items() if not v["passed"]]))
    bal = sum(rules[next(iter(w))]["A_split_b6"]["payment_eur"].values()) + pD[BUNKER] - (I["objective"] - pI.get(SHARED, 0.0))
    res = dict(script=SCRIPT, integrated=str(int_dir), disconnected=str(dis_dir), b6_eur=b6, objective_integrated=I["objective"], objective_disconnected=D["objective"],
               networks=dict(integrated=I.get("solved_network"), integrated_sha256=I.get("solved_network_sha256"), disconnected=D.get("solved_network"),
                             disconnected_sha256=D.get("solved_network_sha256")),
               bunker_player_present=dict(integrated=I.get("bunker_player_present"), disconnected=D.get("bunker_player_present")),
               precision=dict(integrated=I.get("precision"), disconnected=D.get("precision")),
               main_form=main_form,
               owen=dict(form=main_form, sources=dict(integrated=(dI or {}).get("source"), disconnected=(dD or {}).get("source")),
                         usable=dict(integrated=(dI or {}).get("usable"), disconnected=(dD or {}).get("usable")),
                         allocation_integrated_eur=pI, allocation_disconnected_eur=pD,
                         benefit_eur=ben, benefit_interval_eur=rng, negative_benefit=[p for p in PLAYERS if ben[p] < 0],
                         negative_somewhere_in_interval=[p for p in PLAYERS if rng[p]["min"] < 0], sum_players_eur=float(sum(ben.values())),
                         shared_change_eur=float(pD.get(SHARED, 0.0) - pI.get(SHARED, 0.0))),
               market_form=dict(benefit_eur=mben, benefit_interval_eur=mrng, negative_benefit=[p for p in PLAYERS if mben[p] < 0],
                                market_minus_main_benefit_eur={p: mben[p] - ben[p] for p in PLAYERS},
                                note="market-settlement form (current ledger, ALLOCATION.json); differs from the dual form by the KVL loop transfers and KKT residuals"),
               proportional_bases=dict(
                   decision="supplement 01 D4 (item 136): (A) proportional split of B6 (main discussion), tested against the leave-one-out marginal "
                            "contribution; (B) proportional split of the integrated total cost (Young et al.), tested for individual rationality",
                   A="benefit_i = s_i x B6, payment_i = disconnected allocation_i - benefit_i; test: payment_i >= c'(i) (c'(i) = c(N) - c(N - i), D8 "
                     "adjusted), i.e. benefit_i <= disconnected allocation_i - c'(i): otherwise the other players pay more than c(N - i). With B6 > 0 the "
                     "benefit is never negative, so 'negative benefit' is not a test of (A). Only countries with a leave-one-out run.",
                   B="payment_i = s_i x (c(N) - phi_BUNKER - SHARED) of the integrated run; test (individual rationality): payment_i <= disconnected "
                     "allocation_i (+ the C1 (b) tolerance)"),
               loo_check_source=lc_src, tolerance_source=tol_src, owen_checks=owen_chk,
               weights_main=list(WEIGHTS_MAIN), weights_comparison=list(WEIGHTS_COMPARISON),
               weights_note="supplement 01 D5: population AEO8 D.1 (+ UN WPP 2024 TL), GDP AEO8 D.2 (TL by the M08b rule), electricity = the model's fixed / base "
                            "loads (main); SSP2 2050 population and GDP for comparison",
               proportional=rules, socio_sources=sw["sources"], d2_sha256=sw["d2_sha256"], electricity_twh=dict(base=w["electricity_base"], fixed=w["electricity_fixed"]),
               rule_budget_residual_eur=float(bal), fx_per_eur2020=fx,
               notes=["(A) splits B6 among the 11 countries by positive weights: with B6 > 0 no country gets a negative benefit; the bunker account (no "
                      "population / GDP / electricity) keeps its disconnected allocation (benefit 0) in (A) and its integrated allocation in (B)",
                      "rule_budget_residual_eur = sum of the (A) payments of the first weight + bunker - (integrated objective - integrated pool residual) = change of the pool residual"])
    (out / "BENEFIT.json").write_text(json.dumps(res, indent=1, default=str))
    rows = []
    for p in PLAYERS:
        r = dict(player=p, owen_benefit_eur=ben[p], owen_benefit_min_eur=rng[p]["min"], owen_benefit_max_eur=rng[p]["max"], owen_benefit_usd2020=ben[p] * fx,
                 market_form_benefit_eur=mben[p], loo_marginal_cost_eur=(lc.get(p) or {}).get("c_prime"))
        for k, v in rules.items():
            r[f"{k}_A_benefit_eur"] = v["A_split_b6"]["benefit_eur"].get(p, 0.0)
            r[f"{k}_A_loo_passed"] = (v["A_split_b6"]["loo_check"].get(p) or {}).get("passed")
            r[f"{k}_B_payment_eur"] = v["B_split_total"]["payment_eur"].get(p)
            r[f"{k}_B_ir_passed"] = (v["B_split_total"]["ir_check"].get(p) or {}).get("passed")
        rows.append(r)
    pd.DataFrame(rows).set_index("player").to_csv(out / "BENEFIT.csv")
    (out / "BENEFIT.md").write_text(markdown_benefit(res))
    return res


def markdown_benefit(r: dict) -> str:
    o = r["owen"]
    L = ["# BENEFIT（M12 C1 第 4、5 项：受益检查与比例规则对照；只读）", "",
         f"- 一体化：`{r['integrated']}`；不互联：`{r['disconnected']}`。",
         f"- 主值口径（补充 01 D1）：**{r['main_form']}**；来源 {o['sources']['integrated']}；{o['sources']['disconnected']}。",
         f"- B6 = 不互联目标值 − 一体化目标值 = {bn(r['b6_eur'])} bn EUR2020。",
         f"- Owen 受益为负的参与者（α 0.5）：**{', '.join(o['negative_benefit']) or '无'}**；α 区间内可能为负：{', '.join(o['negative_somewhere_in_interval']) or '无'}。",
         f"- 燃料舱参与者：一体化 {r['bunker_player_present']['integrated']}，不互联 {r['bunker_player_present']['disconnected']}。", "",
         "| 参与者 | Owen 受益 bn | 区间下限 | 区间上限 |", "|---|---|---|---|"]
    L += [f"| {p} | {bn(o['benefit_eur'][p])} | {bn(o['benefit_interval_eur'][p]['min'])} | {bn(o['benefit_interval_eur'][p]['max'])} |" for p in PLAYERS]
    ks = list(r["proportional"])
    pb = r["proportional_bases"]; oc = r["owen_checks"]
    L += ["", f"- 权重（补充 01 D5）：主用 {', '.join(r['weights_main'])}；对照 {', '.join(r['weights_comparison'])}（表中排在后面）。"]
    mark = lambda v: "" if v is None else ("" if v else " ✗")   # noqa: E731
    L += ["", "## 比例规则 (A)：按比例分摊 B6（主讨论；检验 = 去一国边际贡献，补充 01 D4）", "", f"- {pb['A']}", f"- 去一国来源：{r['loo_check_source'] or '无（(A) 的检验不可计算）'}；容差：{r['tolerance_source']}。",
          f"- Owen（主值）去一国检查：" + ("；".join(f"{c} 余量 {bn(v['margin_eur'])} bn {'通过' if v['passed'] else '**未通过**'}" for c, v in oc["loo"].items()) or "无去一国运行"), "",
          "| 国 | Owen 受益 | 受益上限 φ不互联 − c′ | " + " | ".join(ks) + " |", "|---|---|---|" + "---|" * len(ks)]
    for c in COUNTRIES:
        la = {k: r["proportional"][k]["A_split_b6"]["loo_check"].get(c) for k in ks}
        cap = next((v["max_benefit_eur"] for v in la.values() if v), None)
        L.append(f"| {c} | {bn(o['benefit_eur'][c])} | {bn(cap)} | " + " | ".join(bn(r["proportional"][k]["A_split_b6"]["benefit_eur"][c]) + mark((la[k] or {}).get("passed")) for k in ks) + " |")
    L += ["", "（✗ = 规则给该国的好处超过其边际贡献，其余参与者合计支付超过 c(N − i)。）", "",
          "(A) 去一国检查未通过：" + "；".join(f"{k}：{', '.join(r['proportional'][k]['A_split_b6']['loo_violations']) or '无'}" for k in ks),
          "", "## 比例规则 (B)：按比例分摊一体化总成本（对照；检验 = 个体理性）", "", f"- {pb['B']}",
          f"- 11 国分摊总额 = {bn(r['proportional'][ks[0]]['B_split_total']['total_eur'])} bn。Owen（主值）个体理性：" +
          ("全部通过" if all(v["passed"] for v in oc["ir"].values()) else "未通过 " + ", ".join(c for c, v in oc["ir"].items() if not v["passed"])), "",
          "| 国 | 不互联分摊 | Owen 支付 | " + " | ".join(ks) + " |", "|---|---|---|" + "---|" * len(ks)]
    for c in COUNTRIES:
        L.append(f"| {c} | {bn(o['allocation_disconnected_eur'][c])} | {bn(o['allocation_integrated_eur'][c])} | "
                 + " | ".join(bn(r["proportional"][k]["B_split_total"]["payment_eur"][c]) + mark(r["proportional"][k]["B_split_total"]["ir_check"][c]["passed"]) for k in ks) + " |")
    L += ["", "（✗ = 支付超过不互联分摊，违反个体理性。）", "",
          "(B) 个体理性未通过：" + "；".join(f"{k}：{', '.join(r['proportional'][k]['B_split_total']['ir_violations']) or '无'}" for k in ks), ""]
    L += [f"- {x}" for x in r["notes"]]
    L += [f"- 预算残差 {r['rule_budget_residual_eur']:,.0f} EUR（池盈余变化）。", f"- 权重来源：{r['socio_sources']}"]
    m = r["market_form"]
    L += ["", "## 并列：市场结算形式（现行账本）下的受益", "", f"- 受益为负：**{', '.join(m['negative_benefit']) or '无'}**", "",
          "| 参与者 | 主值受益 bn | 市场形式受益 bn | 市场 − 主值 bn |", "|---|---|---|---|"]
    L += [f"| {p} | {bn(o['benefit_eur'][p])} | {bn(m['benefit_eur'][p])} | {bn(m['market_minus_main_benefit_eur'][p])} |" for p in PLAYERS]
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------------------------------------------------------------- leave-one-out
def loo(full_dir: Path, loo_dirs: dict, out: Path, reference: Path | None, standalone_dir: Path | None, alpha: float = ALPHA_MAIN) -> dict:
    """C1 item 6: c'(i) = c(N) - c(N - i) from runs of the same resolution and profile; phi_i >= c'(i) within the C1 (b) per-country threshold;
    sign of the indivisible cost c(N) - sum c'(i); SCRB for comparison when all 11 runs are there (standalone cost = the disconnected allocation).
    Supplement 01 D8: c(N - i) gets back the remaining side's share (alpha) of the existing FOM of the corridors removed with i; the check uses the
    adjusted value, the raw one is reported."""
    out.mkdir(parents=True, exist_ok=True)
    F = _alloc_json(full_dir)
    rf = json.loads((Path(full_dir) / "SOLVE_RECEIPT.json").read_text()) if (Path(full_dir) / "SOLVE_RECEIPT.json").exists() else {}
    tol_bn, tol_src = thresholds_bn(Path(full_dir), reference)
    dF = _dual_alloc(full_dir, None)   # supplement 01 D1: the dual form is the main value when the run has it
    phi, it_ = (dF["allocation"], dF.get("interval") or F["interval_eur"]) if dF is not None else (F["allocation_eur"]["0.5"], F["interval_eur"])
    main_form = "owen_dual_form" if dF is not None else "market_settlement_form (no m12_owen/OWEN.json in the full run)"
    c_loo, same = {}, {}
    for c, d in sorted(loo_dirs.items()):
        r = json.loads((Path(d) / "SOLVE_RECEIPT.json").read_text())
        c_loo[c] = float(r["objective"])
        pc_ = precision_context(Path(d))
        same[c] = dict(profile=r.get("solver_profile") == rf.get("solver_profile"),
                       snapshots=(r.get("input_network") or {}).get("snapshots") == (rf.get("input_network") or {}).get("snapshots"),
                       termination=r.get("termination_condition"), input_network=(r.get("input_network") or {}).get("path"),
                       input_network_sha256=(r.get("input_network") or {}).get("sha256"), c1_grade=pc_.get("grade"), c1_accepted=pc_.get("accepted"))
    lines = pd.read_csv(Path(full_dir) / "ALLOCATION_LINES.csv") if (Path(full_dir) / "ALLOCATION_LINES.csv").exists() else pd.DataFrame()
    addback = {}
    for c in c_loo:   # D8: the variant removes the corridors to c with their existing FOM; the remaining side's share (alpha) of it is added back
        q = lines[lines.pair.str.split("|").apply(lambda x: c in x)] if len(lines) else pd.DataFrame(columns=["pair", "fom_existing"])
        other = np.where(q.pair.str.split("|").str[0].to_numpy() == c, 1.0 - alpha, alpha) if len(q) else np.zeros(0)
        addback[c] = float((other * q.fom_existing.to_numpy(dtype=float)).sum()) if len(q) else 0.0
    c_adj = {c: c_loo[c] + addback[c] for c in c_loo}
    tol_e = {c: v * 1e9 for c, v in tol_bn.items()}
    raw = loo_check({p: phi[p] for p in COUNTRIES}, float(F["objective"]), c_loo, tol_e)
    chk = loo_check({p: phi[p] for p in COUNTRIES}, float(F["objective"]), c_adj, tol_e)   # the check uses the adjusted c(N - i)
    chk.update(indivisible_cost_raw=raw["indivisible_cost"], indivisible_cost_sign_raw=raw["indivisible_cost_sign"], all_passed_raw=raw["all_passed"],
               adjustment=f"supplement 01 D8: c(N - i) + the remaining side's share (alpha {alpha:g}) of the existing FOM of the corridors removed with i "
                          "(ALLOCATION_LINES.csv fom_existing), so that c(N - i) has the Owen attribution; raw values kept")
    for c, v in chk["countries"].items():
        r_ = raw["countries"][c]
        v.update(same_profile_and_resolution=same[c], c_N_minus_i_raw=c_loo[c], c_N_minus_i_adjusted=c_adj[c], addback_remaining_side_fom_eur=addback[c],
                 marginal_cost_raw=r_["marginal_cost"], marginal_cost_adjusted=v["marginal_cost"], passed_raw=r_["passed"])
        v["interval_min_eur"] = it_[c]["min"]; v["passed_at_interval_min"] = bool(it_[c]["min"] - v["marginal_cost"] >= -v["tolerance"])
        v["market_form_allocation_eur"] = F["allocation_eur"]["0.5"][c]
        v["market_form_passed"] = bool(F["allocation_eur"]["0.5"][c] - v["marginal_cost"] >= -v["tolerance"])
    res = dict(script=SCRIPT, full=str(full_dir), main_form=main_form, owen_source=(dF or {}).get("source"), loo_runs={c: str(d) for c, d in loo_dirs.items()},
               tolerance_source=tol_src, tolerance_bn=tol_bn,
               objective_full=float(F["objective"]), check=chk, all_11=bool(set(c_loo) == set(COUNTRIES)))
    sa_ok = standalone_dir is not None and (Path(standalone_dir) / "ALLOCATION.json").exists() and json.loads((Path(standalone_dir) / "ALLOCATION.json").read_text()).get("computable")
    if res["all_11"] and sa_ok:   # supplement 01 D6: optional comparison, automatic once all 11 runs exist
        dS = _dual_alloc(standalone_dir, None)
        S = dS["allocation"] if dS is not None else _alloc_json(standalone_dir)["allocation_eur"]["0.5"]
        cN_c = float(F["objective"]) - phi[BUNKER] - phi.get(SHARED, 0.0)
        res["scrb"] = dict(computed=True, standalone_proxy="disconnected-run allocation of the country (proxy, not a strict standalone run; supplement 01 D6)",
                           countries_cost_eur=cN_c,
                           allocation_eur=scrb(cN_c, {c: S[c] for c in COUNTRIES}, {c: chk["countries"][c]["marginal_cost"] for c in COUNTRIES}))
    else:
        res["scrb"] = dict(computed=False, runs=len(c_loo),
                           reason=f"supplement 01 D6: SCRB not computed - {len(c_loo)} leave-one-out run(s), SCRB needs all 11 (third batch: VN, TH, LA only); "
                                  "it is given automatically once all 11 runs and a disconnected allocation exist, with the standalone cost proxied by the "
                                  "disconnected allocation")
    (out / "LOO_CHECK.json").write_text(json.dumps(res, indent=1, default=str))
    L = ["# LOO_CHECK（M12 C1 第 6 项：去一国检查；只读）", "", f"- 全体：`{full_dir}`；容差：{tol_src}。", f"- 分摊口径：{main_form}。",
         f"- c(N − i) 加回（补充 01 D8）：被移出走廊中剩余一方按 α = {alpha:g} 的存量固定运维；检查用加回值，原值并列。",
         f"- 不可分成本 c(N) − Σ c′(i) = {bn(chk['indivisible_cost'])} bn（{chk['indivisible_cost_sign']}；原值 {bn(chk['indivisible_cost_raw'])} bn；仅含已有国家）。", "",
         "| 国 | c(N − i) 原值 bn | 加回 M EUR | c′(i) 加回后 bn | Owen 分摊 bn | 余量 bn | 容差 bn | 通过 | 原值通过 | 区间下限仍通过 | 市场形式通过 | 同档案 / 分辨率 | C1 等级 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c, v in chk["countries"].items():
        sp = v["same_profile_and_resolution"]
        L.append(f"| {c} | {bn(v['c_N_minus_i_raw'])} | {v['addback_remaining_side_fom_eur'] / 1e6:.2f} | {bn(v['marginal_cost'])} | {bn(v['allocation'])} | {bn(v['margin'])} | "
                 f"{v['tolerance'] / 1e9:.4f} | {v['passed']} | {v['passed_raw']} | {v['passed_at_interval_min']} | {v['market_form_passed']} | {sp['profile'] and sp['snapshots']} | {sp.get('c1_grade')} |")
    L += ["", "SCRB（可选对照，补充 01 D6）：" + (json.dumps({k: round(v / 1e9, 3) for k, v in res["scrb"]["allocation_eur"].items()}) + "（单独成本以不互联分摊代理）"
                                               if res["scrb"].get("computed") else f"未计算——只有 {res['scrb']['runs']} 次去一国运行，SCRB 需要全部 11 次；"
                                               "有 11 次时自动给出，单独成本以不互联分摊代理。")]
    (out / "LOO_CHECK.md").write_text("\n".join(L) + "\n")
    return res


def main():
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--repo", type=Path, default=HERE.parent); r.add_argument("--solved", type=Path, default=None)
    r.add_argument("--solve-dir", type=Path, default=None); r.add_argument("--scenario", default="integrated"); r.add_argument("--label", default="")
    r.add_argument("--out", type=Path, default=None); r.add_argument("--register", action="store_true")
    r.add_argument("--precision", type=Path, default=None, help="PRECISION.json when it is not in the solve dir (older runs)")
    b = sub.add_parser("benefit"); b.add_argument("--integrated", type=Path, required=True); b.add_argument("--disconnected", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True); b.add_argument("--repo", type=Path, default=HERE.parent)
    b.add_argument("--integrated-dual", type=Path, default=None); b.add_argument("--disconnected-dual", type=Path, default=None)
    b.add_argument("--loo-check", type=Path, default=None, help="LOO_CHECK.json of the batch (D4 (A): rule benefits vs the leave-one-out marginal contributions)")
    o = sub.add_parser("loo"); o.add_argument("--full", type=Path, required=True); o.add_argument("--loo", action="append", default=[], help="CC=<run dir>")
    o.add_argument("--out", type=Path, required=True); o.add_argument("--reference", type=Path, default=None); o.add_argument("--standalone", type=Path, default=None)
    a = ap.parse_args()
    if a.cmd == "run":
        solved = a.solved
        if solved is None and a.solve_dir is not None:
            solved = next(iter(sorted(a.solve_dir.glob("*_solved.nc"))), None)
        res = run(solved, a.scenario, a.out or a.solve_dir, a.solve_dir, a.label, a.repo, a.register, a.precision)
        print(json.dumps(dict(computable=res.get("computable"), identity=res.get("identity"), checks=res.get("checks")), default=str))
    else:   # batch steps: inputs that are not computable give a short JSON instead of a traceback (the batch continues)
        try:
            if a.cmd == "benefit":
                res = benefit(a.integrated, a.disconnected, a.out, a.repo, a.integrated_dual, a.disconnected_dual, a.loo_check)
                print(json.dumps(dict(b6_bn=res["b6_eur"] / 1e9, negative=res["owen"]["negative_benefit"]), default=str))
            else:
                res = loo(a.full, dict(s.split("=", 1) for s in a.loo), a.out, a.reference, a.standalone)
                print(json.dumps(dict(all_passed=res["check"]["all_passed"], indivisible_sign=res["check"]["indivisible_cost_sign"]), default=str))
        except (ValueError, FileNotFoundError, KeyError) as e:
            a.out.mkdir(parents=True, exist_ok=True)
            name = "BENEFIT.json" if a.cmd == "benefit" else "LOO_CHECK.json"
            (a.out / name).write_text(json.dumps(dict(script=SCRIPT, computable=False, reason=f"{type(e).__name__}: {e}"), indent=1))
            print(json.dumps(dict(computable=False, reason=str(e)[:200])))


if __name__ == "__main__":
    main()
