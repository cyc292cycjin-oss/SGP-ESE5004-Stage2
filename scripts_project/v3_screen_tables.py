"""V3 screening result tables (RUN_PLAN_SCREEN_V3.md section 6, review 2026-11-03 sections 1, 2.4): read-only, no solver. Three tables from the solved runs of the integrated run V1 and the no_new_xb run V2:

    python scripts_project/v3_screen_tables.py --out-dir <run dir> [--runs V1,V2]

  * ID_LEDGER_DECOMPOSITION.csv: the ledger of ID in both runs, grouped by account (electricity, liquid purchases and sales, bunker sales, freight, the rest), with the Owen benefit of ID and BUNKER (review decision 2);
  * VN_BIOMASS_BALANCE.json: fixed demand, potential, overflow, useful heat, pool use from gate B3;
  * LA_EXPORT_UTILISATION.csv: for every Lao country pair the APG lines and the plant lines separately: usable MW, annual export and import, mean use of the usable capacity, hours at the limit.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

GROUPS = {"electricity trade": ("network_trade_AC", "network_trade_DC"), "liquid trade": ("liquid_trade_methanol", "liquid_trade_ammonia", "liquid_trade_oil", "liquid_trade_oil non-fossil"),
          "bunker sales": ("bunker_methanol final energy", "bunker_oil final energy", "bunker_co2 bunkers"), "freight": ("liquid_ship_freight", "liquid_transit_freight", "co2_ship_freight", "co2_transit_freight", "co2_transit_rail_freight", "co2_transit_ship_freight"),
          "pipelines": ("network_trade_H2 pipeline", "network_trade_gas pipeline", "network_trade_CO2 pipeline"), "capex and fixed cost": ("capex_new", "fom_existing", "xb_share_infrastructure_cost", "xb_share_congestion_rent"), "variable cost": ("variable_cost",), "co2 storage": ("co2_storage_service",)}
LIMIT_SHARE = 0.99


def jl(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def id_ledger(out: Path, runs: list) -> pd.DataFrame:
    led = {r: pd.read_csv(out / r / "COUNTRY_COST_LEDGER.csv", index_col=0) for r in runs}; rows = []
    for g, cols in GROUPS.items():
        v = {r: float(sum(led[r].at["ID", c] for c in cols if c in led[r].columns)) / 1e9 for r in runs}
        rows.append(dict(account=g, **v, difference_bn=v[runs[1]] - v[runs[0]]))
    v = {r: float(led[r].at["ID", "total"]) / 1e9 for r in runs}; rows.append(dict(account="total", **v, difference_bn=v[runs[1]] - v[runs[0]]))
    t = pd.DataFrame(rows); c = t[t.account != "total"].difference_bn.sum()
    if abs(c - t[t.account == "total"].difference_bn.iloc[0]) > 1e-6:
        t.loc[len(t)] = dict(account="not grouped", **{r: float("nan") for r in runs}, difference_bn=t[t.account == "total"].difference_bn.iloc[0] - c)
    return t


def vn_biomass(out: Path, runs: list) -> dict:
    res = {}
    for r in runs:
        g = (jl(out / r / "V5_GATES.json") or {}).get("B3") or {}; x = pd.DataFrame(g.get("rows") or [])
        if not len(x):
            res[r] = None
            continue
        x = x[x.country == "VN"]; res[r] = dict(gate_passed=g.get("passed"), potential_twh=float(x.potential_mwh.sum()) / 1e6, used_twh=float(x.used_mwh.sum()) / 1e6, max_store_excess_mwh=float((x.used_mwh - x.potential_mwh).max()), refilled=bool(x.refilled.any()))
    return res


def overflow_ledger(n) -> dict:
    return ((n.meta.get("s2_demand_ledger") or {}).get("industry") or {}).get("biomass_overflow", {}).get("VN") or {}


def la_export(n, run: str) -> pd.DataFrame:
    w = n.snapshot_weightings.generators; c = n.buses.country.astype(str); hours = float(w.sum()); rows = []

    def pair(a, b):
        return "-".join(sorted((c[a], c[b])))

    def add(p, kind, usable, export, imp):
        e = export.mul(w).sum() / 1e6; i = imp.mul(w).sum() / 1e6; net = export + imp
        rows.append(dict(run=run, pair=p, kind=kind, usable_mw=usable, export_twh=float(e), import_twh=float(i), mean_use_of_usable=(float(net.mul(w).sum()) / hours / usable if usable else None), hours_at_limit=(float(w[net >= LIMIT_SHARE * usable].sum()) if usable else 0.0)))

    la = lambda b: c[b] == "LA"
    L = n.lines[n.lines.border_class == "cross_border"]; L = L[[la(a) != la(b) for a, b in zip(L.bus0, L.bus1)]]
    for p, g in L.groupby([pair(a, b) for a, b in zip(L.bus0, L.bus1)]):
        f = pd.DataFrame({k: n.lines_t.p0[k] if la(g.at[k, "bus0"]) else -n.lines_t.p0[k] for k in g.index}); add(p, "APG lines", float((g.s_nom_opt * g.s_max_pu).sum()), f.clip(lower=0.0).sum(axis=1), (-f).clip(lower=0.0).sum(axis=1))
    K = n.links[(n.links.border_class == "cross_border") & (n.links.transport_carrier.astype(str) == "electricity") & ~n.links.index.str.endswith("-reversed")]; K = K[[la(a) != la(b) for a, b in zip(K.bus0, K.bus1)]]
    for p, g in K.groupby([pair(a, b) for a, b in zip(K.bus0, K.bus1)]):
        e = sum((n.links_t.p0[k].clip(lower=0.0) for k in g.index if la(g.at[k, "bus0"])), start=pd.Series(0.0, index=n.snapshots)); i = sum((n.links_t.p0[k + "-reversed"].clip(lower=0.0) for k in g.index if la(g.at[k, "bus0"]) and k + "-reversed" in n.links_t.p0), start=pd.Series(0.0, index=n.snapshots))
        add(p, "plant lines" if (g.carrier == "dedicated plant line").all() else "DC links", float(g.p_nom_opt.sum()), e, i)
    return pd.DataFrame(rows)


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--out-dir", type=Path, required=True); ap.add_argument("--runs", default="V1,V2"); a = ap.parse_args()
    runs = a.runs.split(","); t = id_ledger(a.out_dir, runs); t.to_csv(a.out_dir / "ID_LEDGER_DECOMPOSITION.csv", index=False)
    ben = jl(a.out_dir / "M12_BENEFIT" / "BENEFIT.json") or {}; o = ben.get("owen") or {}; pi, pd_ = o.get("allocation_integrated_eur") or {}, o.get("allocation_disconnected_eur") or {}
    bio = dict(pool=vn_biomass(a.out_dir, runs), owen_bn={k: (pd_[k] - pi[k]) / 1e9 for k in ("ID", "BUNKER", "LA", "TH") if k in pi and k in pd_}); ex = []
    for r in runs:
        f = next(iter(sorted((a.out_dir / r).glob("*_solved.nc"))), None)
        if f is None:
            continue
        n = pypsa.Network(f); bio["overflow_ledger"] = overflow_ledger(n); ex.append(la_export(n, r))
    (a.out_dir / "VN_BIOMASS_BALANCE.json").write_text(json.dumps(bio, indent=1, sort_keys=True, default=str) + "\n")
    if ex:
        pd.concat(ex).to_csv(a.out_dir / "LA_EXPORT_UTILISATION.csv", index=False)
    print(json.dumps(dict(id_difference_bn=float(t[t.account == "total"].difference_bn.iloc[0]), la_rows=sum(len(x) for x in ex), solver_runs=0)))


if __name__ == "__main__":
    main()
