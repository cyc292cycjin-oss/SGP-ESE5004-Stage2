"""S4D-3 (decision 91a): country cost ledger, identity gate B16_LEDGER and nodal prices (post-solve, read-only on the solved network).

Ledger rules (one set for both scenarios; registry fragment s4d_3):
  * every objective term is a direct cost of the entity that owns the component - capital cost of the new capacity (p_nom_opt - p_nom for
    extendable components), marginal cost x flow x snapshot weight, and the fixed-once constants (existing_annual_fixed_om_eur of the existing
    assets, existing cross-border FOM): the same decomposition as gate A5. Owners: one-port components -> entity of their bus; domestic lines /
    links -> their country; cross-border lines / links (border_class cross_border) -> the corridor of the two countries; CO2 shipping (border_class
    maritime_trade, decision 92) -> the exporter (freight); links touching only regional buses -> the ASEAN pool or the ASEAN bunker account.
  * bus entities: national buses -> their country; the regional liquid buses (decision 44: ASEAN oil, oil non-fossil, methanol, ammonia) -> the
    ASEAN pool; the bunker load buses and 'co2 bunkers ASEAN' (decision 88) -> the ASEAN bunker account (separate subject, no country).
  * whenever a component port sits on a bus of another entity, the flow is settled at that bus's dual (buses_t.marginal_price x weight): the
    owner pays for withdrawals and is paid for injections, the bus entity the opposite. Hence: cross-border exchanges at each end's nodal dual;
    liquid-fuel purchases / sales of a country at the pool dual; bunker fuel at the pool dual; the storage service of shipped CO2 at the
    receiver's 'co2 sequestered <j>' dual (exporter pays, receiver is paid).
  * corridor entities (capital, existing FOM, operating cost, and the congestion rent = their settlement surplus) are split between the two
    countries: half / half (main) or by in-country length (sensitivity, XB_LENGTH_SHARES_S4D3.csv).
  * settlements are transfers between entities and cancel; therefore sum(countries) + bunker account = objective - pool surplus. The ASEAN pool
    has no owner in the rules: its surplus (settlement income minus its own costs, i.e. the rents of binding limits on regional supply) is the
    difference term of the identity and is reported. Domestic gas is a country cost at the decision-43 price (it is the producing generator's
    marginal cost).
  * gate B16_LEDGER: |sum(countries) + bunker - objective| <= 1e-6 x |objective| (objective incl. the fixed-once constants, as reported).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

POOL, BUNKER = "ASEAN_POOL", "ASEAN_BUNKER"
REL_TOL = 1e-6
ROOT = Path(__file__).resolve().parents[1]
ONE_PORT = {"Generator": ("p", -1.0), "Store": ("p", -1.0), "StorageUnit": ("p", -1.0), "Load": ("p", 1.0)}   # withdrawal = sign x p
FLOW = {"Generator": "p", "Link": "p0", "Store": "p", "StorageUnit": "p_dispatch"}   # flows that carry marginal_cost (gate A5)
NOM = {"Generator": "p_nom", "Link": "p_nom", "Line": "s_nom", "StorageUnit": "p_nom", "Store": "e_nom"}


def bus_entities(n) -> pd.Series:
    from s4c_layers import BUNKER_CO2_BUS
    bunker = {BUNKER_CO2_BUS} | {str(v.get("bus")) for v in n.meta.get("research_bunkers", {}).get("asean_loads", {}).values() if isinstance(v, dict)}
    c = n.buses.country.astype(str)
    return pd.Series(np.where(c != "ASEAN", c, np.where(n.buses.index.isin(list(bunker)), BUNKER, POOL)), index=n.buses.index)


def _ports(df):
    return sorted([c for c in df.columns if c.startswith("bus") and c[3:].isdigit()], key=lambda c: int(c[3:]))


def owners(n, ent: pd.Series) -> dict:
    """component type -> Series of owner entity; corridor owners are 'XB:<A>|<B>'. One-port components belong to the country of their
    country column when it names a country (e.g. the national industry ammonia loads on the regional 'ASEAN ammonia' bus), else to the
    entity of their bus."""
    from carrier_architecture import COUNTRIES
    atmo = set(n.buses.index[n.buses.carrier == "co2"]) | set(n.buses.index[n.buses.index.str.startswith("co2 atmosphere")])
    out = {}
    for t in ONE_PORT:
        d = n.df(t); be = d.bus.map(ent)
        c = d.country.astype(str) if "country" in d else pd.Series("", index=d.index)
        out[t] = c.where(c.isin(list(COUNTRIES)), be)
    for t in ("Line", "Link"):
        df = n.df(t); own = {}
        for name, z in df.iterrows():
            ports = [z[p] for p in _ports(df) if isinstance(z[p], str) and z[p]]
            bc = str(z.get("border_class", "domestic"))
            nat = sorted({ent[b] for b in ports if ent[b] not in (POOL, BUNKER) and b not in atmo})
            if bc == "cross_border":
                if len(nat) != 2:
                    raise ValueError(f"cross-border {t} {name} without two countries: {nat}")
                own[name] = f"XB:{nat[0]}|{nat[1]}@{t}:{name}"
            elif bc == "maritime_trade":
                own[name] = ent[z.bus0]
            elif nat:
                if len(nat) != 1:
                    raise ValueError(f"domestic {t} {name} with ports in {nat}")
                own[name] = nat[0]
            else:
                own[name] = BUNKER if any(ent[b] == BUNKER for b in ports) else POOL
        out[t] = pd.Series(own, dtype=object).reindex(df.index)
    return out


def _subject_settlement(owner, bus_ent, bus, n, comp_carrier, border_class):
    car = str(n.buses.at[bus, "carrier"])
    if bus_ent == POOL:
        return f"liquid_pool_{car}"
    if bus_ent == BUNKER:
        return f"bunker_{car}"
    if car == "co2 sequestered":
        return "co2_storage_service"
    if owner.startswith("XB:"):
        return f"network_trade_{comp_carrier}"
    return "other_settlement"


def country_cost_ledger(n, length_shares: pd.DataFrame | None = None, extra_terms: dict | None = None):
    """Returns (long ledger: entity, subject, carrier, eur, eur_length_split; identity dict; diagnostics). extra_terms: objective terms that
    no component carries (the gap-diagnostic slack penalty), booked to the entity OBJECTIVE_EXTRA and counted in the identity."""
    w = n.snapshot_weightings.objective
    ent = bus_entities(n); own = owners(n, ent)
    price = n.buses_t.marginal_price
    rows = []

    def add(entity, subject, carrier, eur):
        if eur != 0.0 and np.isfinite(eur):
            rows.append((entity, subject, str(carrier), float(eur)))
    # direct costs (gate A5 decomposition)
    for t, nom in NOM.items():
        d = n.df(t)
        if not len(d):
            continue
        ext = d[nom + "_extendable"]
        cap = ((d[nom + "_opt"] - d[nom]) * d.capital_cost).where(ext, 0.0)
        for name, v in cap[cap != 0].items():
            add(own[t][name], "capex_new", d.at[name, "carrier"], v)
        if "existing_annual_fixed_om_eur" in d:
            fom = pd.to_numeric(d.existing_annual_fixed_om_eur, errors="coerce").fillna(0.0)
            for name, v in fom[fom != 0].items():
                add(own[t][name], "fom_existing", d.at[name, "carrier"], v)
        if t in FLOW:
            mc = n.get_switchable_as_dense(t, "marginal_cost")
            flow = n.pnl(t)[FLOW[t]].reindex(columns=mc.columns, fill_value=0.0)
            var = (flow * mc).mul(w, axis=0).sum()
            for name, v in var[var != 0].items():
                car = str(d.at[name, "carrier"])
                subj = {"CO2 ship": "co2_ship_freight", "CO2 transit export extra-ASEAN": "co2_transit_freight", "CO2 transit ship": "co2_transit_ship_freight",
                        "CO2 transit rail": "co2_transit_rail_freight"}.get(car, "variable_cost")   # S4F-2 c (97 c): Lao rail transit into the VN store
                add(own[t][name], subj, car, v)
    xb_led = pd.DataFrame(n.meta.get("existing_cross_border_fom_ledger", []))
    for _, r in xb_led.iterrows():
        add(own[r.component_type][r.component], "fom_existing", n.df(r.component_type).at[r.component, "carrier"], float(r.annual_fom_eur))
    # settlements at the dual of the port bus
    reowned = {}
    for t, (attr, sign) in ONE_PORT.items():
        d = n.df(t)
        if not len(d):
            continue
        cross = list(d.index[own[t] != d.bus.map(ent)])
        reowned[t] = len(cross)
        if not cross:
            continue
        flows = n.pnl(t)[attr].reindex(columns=cross, fill_value=0.0) * sign   # withdrawal from the bus
        lam = price[list(d.bus[cross])].to_numpy()
        val = (flows.to_numpy() * lam * w.to_numpy()[:, None]).sum(axis=0)
        for x, v in zip(cross, val):
            if v == 0.0:
                continue
            o, b = own[t][x], d.at[x, "bus"]
            subj = _subject_settlement(o, ent[b], b, n, d.at[x, "carrier"], "")
            add(o, subj, d.at[x, "carrier"], v); add(ent[b], subj, d.at[x, "carrier"], -v)
    for t in ("Line", "Link"):
        d = n.df(t)
        for p in _ports(d):
            k = p[3:]; pn = n.pnl(t).get("p" + k)
            if pn is None or not len(d):
                continue
            buses = d[p]
            sel = [x for x in d.index if isinstance(buses[x], str) and buses[x] and ent[buses[x]] != own[t][x]]
            if not sel:
                continue
            flows = pn.reindex(columns=sel, fill_value=0.0)
            lam = price[[buses[x] for x in sel]].to_numpy()
            val = (flows.to_numpy() * lam * w.to_numpy()[:, None]).sum(axis=0)   # owner pays for withdrawals (p > 0) at the bus dual
            for x, v in zip(sel, val):
                if v == 0.0:
                    continue
                o, b = own[t][x], buses[x]; be = ent[b]
                subj = _subject_settlement(o, be, b, n, d.at[x, "carrier"], d.at[x, "border_class"] if "border_class" in d else "")
                add(o, subj, d.at[x, "carrier"], v)
                add(be, subj, d.at[x, "carrier"], -v)
    for k in extra_terms or {}:   # objective terms outside the components (gap diagnostic slack penalty): own entity, counted in the identity
        add("OBJECTIVE_EXTRA", k, "", float(extra_terms[k]))
    L = pd.DataFrame(rows, columns=["entity", "subject", "carrier", "eur"])
    # corridor entities (one per cross-border component) -> countries: half / half (main) and in-country length shares (sensitivity)
    xb = L[L.entity.str.startswith("XB:")].copy()
    xb["pair"] = xb.entity.str.split("@").str[0]; xb["component"] = xb.entity.str.split("@").str[1]
    out = L[~L.entity.str.startswith("XB:")].copy(); out["eur_length_split"] = out.eur
    shares = {}
    if length_shares is not None and len(length_shares):
        for _, r in length_shares.iterrows():
            shares[f"{r.component_type}:{r.component}"] = {str(r.country_a): float(r.share_a), str(r.country_b): float(r.share_b)}
    add_rows = []; missing = set()
    for (pair, comp, subj, car), v in xb.groupby(["pair", "component", "subject", "carrier"]).eur.sum().items():
        a, b = pair[3:].split("|")
        sh = shares.get(comp)
        if sh is None or set(sh) != {a, b}:
            missing.add(comp); sh = {a: 0.5, b: 0.5}
        s2 = "xb_share_infrastructure_cost" if subj in ("capex_new", "fom_existing", "variable_cost") else "xb_share_congestion_rent"
        add_rows += [(a, s2, car, 0.5 * v, sh[a] * v), (b, s2, car, 0.5 * v, sh[b] * v)]
    xb_rows = pd.DataFrame(add_rows, columns=["entity", "subject", "carrier", "eur", "eur_length_split"])
    out = pd.concat([x for x in (out, xb_rows) if len(x)], ignore_index=True)
    out = out.groupby(["entity", "subject", "carrier"], as_index=False)[["eur", "eur_length_split"]].sum()
    tot = out.groupby("entity")[["eur", "eur_length_split"]].sum()
    special = (POOL, BUNKER, "OBJECTIVE_EXTRA")
    countries = [e for e in tot.index if e not in special]
    obj = float(n.objective)
    side = lambda col: sum(float(tot.at[e, col]) for e in (BUNKER, "OBJECTIVE_EXTRA") if e in tot.index)
    s_main = float(tot.loc[countries, "eur"].sum()) + side("eur")
    s_len = float(tot.loc[countries, "eur_length_split"].sum()) + side("eur_length_split")
    pool = float(tot.at[POOL, "eur"]) if POOL in tot.index else 0.0
    DIRECT = ["capex_new", "fom_existing", "variable_cost", "co2_ship_freight", "co2_transit_freight", "co2_transit_ship_freight"] + list(extra_terms or {})
    direct = float(L[L.subject.isin(DIRECT)].eur.sum())
    settle = float(L[~L.subject.isin(DIRECT)].eur.sum())
    xb_net = xb.groupby("pair").eur.sum()
    xb_rent = xb[xb.subject.str.startswith("network_trade")].groupby("pair").eur.sum()
    xb_cost = xb[~xb.subject.str.startswith("network_trade")].groupby("pair").eur.sum()
    identity = dict(objective=obj, countries_plus_bunker=s_main, countries_plus_bunker_length_split=s_len, difference=s_main - obj,
                    relative_error=abs(s_main - obj) / max(1.0, abs(obj)), relative_error_length_split=abs(s_len - obj) / max(1.0, abs(obj)), tolerance=REL_TOL,
                    difference_sources=dict(asean_pool_surplus=-pool, direct_costs_minus_objective=direct - obj, settlement_sum=settle),
                    countries=len(countries), extra_terms={k: float(v) for k, v in (extra_terms or {}).items()})
    diag = dict(corridors={e: dict(costs=float(xb_cost.get(e, 0.0)), settlement=float(xb_rent.get(e, 0.0)), net=float(xb_net.get(e, 0.0))) for e in sorted(xb_net.index)},
                length_shares_missing=sorted(missing) if length_shares is not None else "not_supplied",
                pool=dict(net=pool, by_subject={k: float(v) for k, v in L[L.entity == POOL].groupby("subject").eur.sum().items()}),
                one_port_owned_by_country_column=reowned)
    return out, identity, diag


def ledger_gate(identity: dict) -> dict:
    ok = bool(identity["relative_error"] <= identity["tolerance"])
    return dict(gate="B16_LEDGER", passed=ok, relative_error=identity["relative_error"], tolerance=identity["tolerance"], objective=identity["objective"],
                countries_plus_bunker=identity["countries_plus_bunker"], difference=identity["difference"], difference_sources=identity["difference_sources"])


def load_length_shares(path: Path | None = None) -> pd.DataFrame | None:
    p = path or next((q for q in (ROOT / "research_inputs/corridors/XB_LENGTH_SHARES_S4F2.csv", ROOT / "research_inputs/corridors/XB_LENGTH_SHARES_S4E1.csv",
                                  ROOT / "research_inputs/corridors/XB_LENGTH_SHARES_S4D3.csv") if q.exists()), None)   # S4F-2 superset first (new #4 end, optional SG-VN / SG-KH)
    if p is None:
        return None
    return pd.read_csv(p) if Path(p).exists() else None


def ledger_table(L: pd.DataFrame) -> pd.DataFrame:
    """Country x subject table (main split) with totals; the length-split total as an extra column."""
    t = L.pivot_table(index="entity", columns="subject", values="eur", aggfunc="sum", fill_value=0.0)
    t["total"] = t.sum(axis=1)
    t["total_length_split"] = L.groupby("entity").eur_length_split.sum().reindex(t.index)
    return t


def nodal_prices(n, freq: str = "D") -> pd.DataFrame:
    """One row per bus (node x carrier): node, carrier, country, snapshot-weighted mean / min / max of the dual price over the run, then one
    column per calendar day (freq 'D') with the snapshot-weighted mean of that day (weights = snapshot_weightings.objective). Units: EUR per
    unit of the bus carrier (MWh, t). Wide layout: 365 x 24 h -> 2,914 rows x 371 columns."""
    w = n.snapshot_weightings.objective; mp = n.buses_t.marginal_price
    per = mp.index.to_period(freq).astype(str) if isinstance(mp.index, pd.DatetimeIndex) else pd.Index(["all"] * len(mp))
    day = mp.mul(w, axis=0).groupby(per).sum().div(w.groupby(per).sum(), axis=0).T
    meta = n.buses.reindex(mp.columns)
    head = pd.DataFrame(dict(node=(meta.location if "location" in meta else pd.Series("", index=meta.index)).astype(str), carrier=meta.carrier, country=meta.country,
                             mean=(mp.mul(w, axis=0).sum() / w.sum()), min=mp.min(), max=mp.max()), index=mp.columns)
    out = pd.concat([head, day], axis=1); out.index.name = "bus"
    return out
