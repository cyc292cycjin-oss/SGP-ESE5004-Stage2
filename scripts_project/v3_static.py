"""V3 static checks (instruction phase 3 item 2; S4I list). No solve.

    PYTHONHASHSEED=0 python scripts_project/v3_static.py --dir <v3 builds dir> --v2 <v2 integrated_2920_3h_unsolved.nc> --out <deliverable dir>

Structure of --dir: integrated/integrated_{2920_3h,365_24h}_unsolved.nc, no_new_xb/no_new_xb_{2920_3h,365_24h}_unsolved.nc. Writes evidence/V3_STATIC_CHECK.json,
evidence/V3_STRUCT_DIFF_V2.csv (v3 against the v2 DFX build, by component type and carrier), evidence/DEMAND_NETWORK_CHECK_V3.csv.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from v3_layers import LOAD_CARRIERS, SHIP_CARRIERS, TRANSIT_CARRIER   # noqa: E402

COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
ATTR = {"Generator": ["bus", "carrier", "p_nom", "p_nom_min", "p_nom_max", "p_nom_extendable", "marginal_cost", "capital_cost", "efficiency"],
        "Link": ["bus0", "bus1", "bus2", "bus3", "bus4", "carrier", "p_nom", "p_nom_min", "p_nom_max", "p_nom_extendable", "marginal_cost", "capital_cost", "efficiency", "efficiency2", "efficiency3", "efficiency4", "p_min_pu", "p_max_pu"],
        "Line": ["bus0", "bus1", "s_nom", "s_nom_min", "s_nom_max", "s_nom_extendable", "capital_cost", "x", "r", "b", "length"],
        "Store": ["bus", "carrier", "e_nom", "e_nom_max", "e_nom_extendable", "capital_cost", "marginal_cost", "e_cyclic"],
        "StorageUnit": ["bus", "carrier", "p_nom", "p_nom_extendable", "capital_cost", "marginal_cost", "max_hours", "efficiency_store", "efficiency_dispatch"],
        "Load": ["bus", "carrier", "p_set"], "Bus": ["carrier", "country"]}
# carriers whose existing components may change between v2 and v3 (V3_RULES section 9); anything else fails
ALLOWED_CHANGED = {"Load": {"industry heat", "industry heat medium A", "industry heat medium B", "industry heat high", "coal final energy", "oil final energy", "gas final energy", "biomass final energy", "industry electricity", "industry hydrogen", "industry ammonia", "industry methanol", "land transport EV",
                            "shipping methanol", "oil feedstock", "gas feedstock", "coal feedstock"},
                   "Generator": {"process emissions"},
                   "Link": {"oil pool", "Haber-Bosch", "ammonia cracker", "methanolisation", "biomass-to-methanol", "OCGT methanol", "industry methanol", "shipping methanol", "BEV charger", "oil final-energy accounting"},
                   "Bus": {"oil final energy", "shipping methanol", "methanol final energy"}}
# "oil pool" in Link: distribution links of the nodes that first get a fossil oil bus because the facility allocation places oil final demand there (decision 164; v2 had only their non-fossil bus)
ALLOWED_NEW = {"Bus": {"oil", "oil non-fossil", "methanol", "ammonia", "methanol final energy", "coal final energy", "gas final energy", "biomass final energy", "oil final energy", "gas feedstock", "coal feedstock", "oil feedstock"},
               "Generator": {"oil import", "methanol import", "ammonia import", "FT fuel import", "process emissions"},
               "Store": {"ammonia store", "methanol store", "oil non-fossil store", "EV battery"},
               "Link": {"oil non-fossil ship", "methanol ship", "ammonia ship", TRANSIT_CARRIER, "oil pool", "shipping methanol", "coal final-energy accounting", "gas final-energy accounting", "biomass final-energy accounting", "oil final-energy accounting", "gas feedstock", "coal feedstock", "oil feedstock", "industry methanol", "industry biomass CC"},
               "Load": ALLOWED_CHANGED["Load"]}


def same(a: pd.Series, b: pd.Series) -> pd.Series:
    if a.dtype == object or b.dtype == object:
        return a.astype(str).replace("nan", "") == b.astype(str).replace("nan", "")
    return pd.Series(np.isclose(a.astype(float), b.astype(float), rtol=1e-12, atol=1e-9, equal_nan=True), index=a.index)


def struct_diff(a, b, label_a="v2", label_b="v3") -> tuple[pd.DataFrame, list]:
    rows, bad = [], []
    for typ, cols in ATTR.items():
        x, y = a.df(typ), b.df(typ)
        gone, new = x.index.difference(y.index), y.index.difference(x.index); both = x.index.intersection(y.index)
        for k, v in x.loc[gone].carrier.astype(str).value_counts().items():
            rows.append(dict(type=typ, change="removed", carrier=k, count=int(v), example=str(x.loc[gone][x.loc[gone].carrier == k].index[0])))
        for k, v in y.loc[new].carrier.astype(str).value_counts().items():
            rows.append(dict(type=typ, change="added", carrier=k, count=int(v), example=str(y.loc[new][y.loc[new].carrier == k].index[0])))
            if k not in ALLOWED_NEW.get(typ, set()):
                bad.append(f"added {typ} {k}")
        for col in cols:
            if col not in x or col not in y:
                continue
            ch = both[~same(x.loc[both, col], y.loc[both, col]).to_numpy()]
            for k, v in y.loc[ch].carrier.astype(str).value_counts().items() if len(ch) and "carrier" in y else []:
                rows.append(dict(type=typ, change=f"attr:{col}", carrier=k, count=int(v), example=str(ch[0])))
                if k not in ALLOWED_CHANGED.get(typ, set()):
                    bad.append(f"changed {typ} {col} {k}")
        for attr, frame_a in a.pnl(typ).items():
            frame_b = b.pnl(typ).get(attr)
            if frame_b is None or not len(frame_a.columns) or "Output" in str(a.df(typ).columns.name):
                continue
            cm = frame_a.columns.intersection(frame_b.columns)
            if len(cm):
                d = (frame_a[cm] - frame_b[cm]).abs().max()
                ch = d.index[d > 1e-9 * frame_a[cm].abs().max().clip(lower=1.0)]
                for k, v in y.loc[y.index.intersection(ch)].carrier.astype(str).value_counts().items():
                    rows.append(dict(type=typ, change=f"series:{attr}", carrier=k, count=int(v), example=str(ch[0])))
                    if k not in ALLOWED_CHANGED.get(typ, set()):
                        bad.append(f"series {typ} {attr} {k}")
    return pd.DataFrame(rows), sorted(set(bad))


def scenario_diff(i, r) -> dict:
    """The integrated and no_new_xb networks: removed components only cross-border, changed attributes only on the kept cross-border stock."""
    bad, removed = [], {}
    for typ in ATTR:
        x, y = i.df(typ), r.df(typ)
        gone = x.index.difference(y.index); removed[typ] = int(len(gone))
        if len(y.index.difference(x.index)):
            bad.append(f"{typ} added in no_new_xb")
        if len(gone) and "border_class" in x and not (x.loc[gone, "border_class"] == "cross_border").all():
            bad.append(f"{typ} non cross-border removed")
        both = y.index
        for col in ATTR[typ]:
            if col in x and col in y:
                ch = both[~same(x.loc[both, col], y.loc[both, col]).to_numpy()]
                if len(ch) and ("border_class" not in y or not (y.loc[ch, "border_class"] == "cross_border").all()):
                    bad.append(f"{typ} {col} changed outside cross-border: {list(ch[:3])}")
    return dict(passed=not bad, removed=removed, problems=bad[:20])


def demand_check(n) -> pd.Series:
    """annual TWh by country and carrier, all sectors (the network writes the final-energy sectors in lower case and the others as in the table; bunker loads carry the tag ASEAN and stay on the nodes of their country)"""
    w = n.snapshot_weightings.generators; p = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum() / 1e6
    tag = n.loads.country.astype(str); country = tag.where(tag != "ASEAN", n.loads.bus.astype(str).str[:2])
    return n.loads.assign(twh=p.reindex(n.loads.index).fillna(0.0), country=country).groupby(["country", "carrier"]).twh.sum()


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", type=Path, required=True); ap.add_argument("--v2", type=Path, required=True); ap.add_argument("--out", type=Path, required=True); a = ap.parse_args()
    from v5.v5_gates import gate_b5_no_new_xb
    I3 = pypsa.Network(str(a.dir / "integrated/integrated_2920_3h_unsolved.nc")); R3 = pypsa.Network(str(a.dir / "no_new_xb/no_new_xb_2920_3h_unsolved.nc")); V2 = pypsa.Network(str(a.v2))
    I1 = pypsa.Network(str(a.dir / "integrated/integrated_365_24h_unsolved.nc")); R1 = pypsa.Network(str(a.dir / "no_new_xb/no_new_xb_365_24h_unsolved.nc"))
    res = {}
    for lab, n, wv in (("integrated_2920", I3, 3.0), ("no_new_xb_2920", R3, 3.0), ("integrated_365", I1, 24.0), ("no_new_xb_365", R1, 24.0)):
        z = {}
        z["weights"] = bool(np.all(n.snapshot_weightings.objective.to_numpy() == wv)); z["hours"] = float(n.snapshot_weightings.objective.sum())
        ports = pd.concat([n.df(t)[c] for t in ("Generator", "Load", "Store", "StorageUnit") for c in ["bus"]] + [n.links[c] for c in n.links if c.startswith("bus") and c[3:].isdigit()] + [n.lines.bus0, n.lines.bus1]).astype(str)
        orphan = sorted(set(n.buses.index) - set(ports)); z["orphan_buses"] = orphan[:10]; z["orphan_count"] = len(orphan)
        z["duplicates"] = {t: int(n.df(t).index.duplicated().sum()) for t in ATTR}
        L = n.links; eff = L.efficiency.astype(float)
        z["efficiency_range"] = [float(eff.min()), float(eff.max())]
        z["p_max_pu_ok"] = bool(((n.get_switchable_as_dense("Link", "p_max_pu").to_numpy() >= -1e-12) & (n.get_switchable_as_dense("Link", "p_max_pu").to_numpy() <= 1 + 1e-12)).all())
        z["ship_links"] = {k: int((L.carrier == v).sum()) for k, v in SHIP_CARRIERS.items()}; z["transit_links"] = int((L.carrier == TRANSIT_CARRIER).sum())
        z["national_buses"] = int(sum(f"{c} {k}" in n.buses.index for c in COUNTRIES for k in LOAD_CARRIERS)); z["asean_liquid_buses"] = [b for b in ("ASEAN oil", "ASEAN oil non-fossil", "ASEAN methanol", "ASEAN ammonia") if b in n.buses.index]
        lk = L[L.carrier == "oil final-energy accounting"]
        fossil = lk[lk.bus0.astype(str).str.endswith(" oil") & ~lk.bus0.astype(str).str.endswith("non-fossil")]
        atm = fossil.bus2.astype(str)
        z["fossil_oil_meters"] = dict(total=int(len(fossil)), to_country_atmosphere=int(atm.str.startswith("co2 atmosphere").sum()), to_bunker_account=int((atm == "co2 bunkers ASEAN").sum()), other=sorted(set(atm[~atm.str.startswith("co2 atmosphere") & (atm != "co2 bunkers ASEAN")]))[:5])
        z["maritime_trade"] = L[L.border_class == "maritime_trade"].carrier.astype(str).value_counts().to_dict()
        z["bunker_loads"] = dict(count=int((n.loads.country.astype(str) == "ASEAN").sum()), buses_in_asean_tag=int(n.loads[n.loads.country.astype(str) == "ASEAN"].bus.map(n.buses.country).eq("ASEAN").all()))
        z["ev"] = dict(stores=int((n.stores.carrier == "EV battery").sum()), v2g=int(L.carrier.astype(str).str.contains("V2G").sum()), charger_extendable=int(L[L.carrier == "BEV charger"].p_nom_extendable.sum()), load_series=int(n.loads.index[n.loads.carrier == "land transport EV"].isin(n.loads_t.p_set.columns).sum()))
        z["slack_generators"] = int(n.generators.carrier.astype(str).str.contains("slack").sum())
        res[lab] = z
    res["gate_b5_no_new_xb"] = gate_b5_no_new_xb(I3, R3)
    res["gate_b5_no_new_xb_365"] = gate_b5_no_new_xb(I1, R1)
    res["scenario_difference_2920"] = scenario_diff(I3, R3); res["scenario_difference_365"] = scenario_diff(I1, R1)
    D, bad = struct_diff(V2, I3); (a.out / "evidence").mkdir(exist_ok=True); D.to_csv(a.out / "evidence/V3_STRUCT_DIFF_V2.csv", index=False)
    res["structure_vs_v2"] = dict(passed=not bad, unexpected=bad[:40], rows=int(len(D)))
    t = pd.read_csv(a.out / "DEMAND_BY_COUNTRY_SECTOR_CARRIER_v3.csv"); ti = t.groupby(["country", "carrier"]).twh.sum()
    NET = ["integrated_2920", "no_new_xb_2920", "integrated_365", "no_new_xb_365"]
    rows = pd.DataFrame(dict(table=ti, integrated_2920=demand_check(I3), no_new_xb_2920=demand_check(R3), integrated_365=demand_check(I1), no_new_xb_365=demand_check(R1))).fillna(0.0).reset_index()
    rows.to_csv(a.out / "evidence/DEMAND_NETWORK_CHECK_V3.csv", index=False)
    from phase4_static import config
    eff = float(config(HERE.parent, "integrated")["research"]["s2"]["industry"]["biomass_overflow_useful_heat_efficiency"])
    heat = rows.carrier.astype(str).str.startswith("industry heat"); bio = rows.carrier == "biomass final energy"
    rel = rows[~heat & ~bio]; dev = float(max((rel[c] - rel.table).abs().max() for c in NET))   # TWh; the table is stored rounded to about 1e-9 TWh
    # biomass above the national potential leaves the biomass load and returns as useful heat at the overflow efficiency (v2 rule, decision 133)
    b = rows[bio].set_index("country"); ov = pd.DataFrame({c: b.table - b[c] for c in NET})
    dh = rows[heat].groupby("country")[NET].sum().sub(rows[heat].groupby("country").table.sum(), axis=0)
    closure = float((dh - ov.reindex(dh.index).fillna(0.0) * eff).abs().max().max())
    res["demand_vs_table"] = dict(max_abs_gap_non_overflow_carriers_twh=dev, overflow_closure_max_twh=closure, passed=bool(dev <= 1e-6 and closure <= 1e-6), useful_heat_efficiency=eff,
                                  country_biomass_overflow_twh={k: float(v) for k, v in ov.integrated_2920.round(6).items() if abs(v) > 1e-6})
    res["all_structural_passed"] = bool(res["gate_b5_no_new_xb"]["passed"] and res["gate_b5_no_new_xb_365"]["passed"] and res["scenario_difference_2920"]["passed"] and res["scenario_difference_365"]["passed"] and res["structure_vs_v2"]["passed"] and res["demand_vs_table"]["passed"] and all(res[k]["weights"] and res[k]["orphan_count"] == 0 for k in ("integrated_2920", "no_new_xb_2920", "integrated_365", "no_new_xb_365")))
    (a.out / "evidence/V3_STATIC_CHECK.json").write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({k: res[k] for k in ("gate_b5_no_new_xb", "scenario_difference_2920", "structure_vs_v2", "demand_vs_table", "all_structural_passed")}, indent=0, default=str)[:3000])
    print(json.dumps(res["integrated_2920"], indent=0, default=str)[:1800])


if __name__ == "__main__":
    main()
