"""V4 D2a section 5 (copies of D1 scripts/d1_static.py C1-C6 and d1_static_extra.py C8, D2a expectations): static checks of the rebuilt v4 main networks
(no solver). Writes STATIC_CHECKS.json and evidence/D2A_NETWORK_DIFF.json into the delivery folder.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/d2a_static.py

  C1 industry electricity / heat loads per country = INDUSTRY_2050_SUMMARY_V4.csv; profiled load means = constants; 365x24h = 2920x3h totals
  C2 EV load = ATS land fuel x the unrounded registry factor; rail = RailNonElectric rows; no parent row
  C3 solid-biomass pools: fixed demand / pool <= 0.99; VN slack >= 1 %; no pool at or above 0.999 that was not there in D1
  C4 domestic gas caps = GAS_PRODUCTION_CAPS_2050_V4.csv (generator count = D1)
  C5 curves (peak / mean; ID three time zones)
  C6 v4 identity: n.meta v4_w08 switch SHA = the table folder (biomass_potential v4_adjusted_t04, meoh_per_tco2 stoichiometric)
  C8 network difference D2a vs D1 (2920x3h and 365x24h): every component table and time series value by value, classified into the EXPECTED set of
     section 3 (EFB / residue pools, the TH2 4 PHS group and the new reservoir, TH reservoir inflows re-shared, methanolisation efficiency3 and the
     fuel-carbon port efficiency4) - anything else is listed as UNEXPECTED (stop condition of the instruction)
  C10 the overflow ledger of the network = INDUSTRY_2050_SUMMARY_V4.csv (Fable F-05)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

sys.path.insert(0, "/home/jin/wt_v4_d2a/scripts_project")
W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_d2a")
B = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d2a/builds/main")
B1 = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d1/builds/main")
PHS_OLD = "existing_survivor::TH2 4::Hydro::6b2ad09f452a"; HYD_NEW = "existing_survivor::TH2 4::hydro existing::D2A"


def annual(n, names) -> pd.Series:
    w = n.snapshot_weightings.objective
    return pd.Series({l: (float((n.loads_t.p_set[l] * w).sum()) if l in n.loads_t.p_set.columns else float(n.loads.at[l, "p_set"]) * float(w.sum())) for l in names}, dtype=float)


def check(tag, n, n365, n1) -> dict:
    from s2_layers import HEAT_BAND_ACCOUNT
    from v4_common import V4_DIR, switch_sha
    from v4_industry import EV_FACTOR
    od = R / n.meta["v4_w08"]["tables_dir"]
    S = pd.read_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
    L = n.loads; res = {}
    acc = {"IndustryElectricityRoutes": "pe_electricity_mwh", "IndustryLowTemperatureHeat": "pe_heat_mwh", **{a: f"pe_heat_{b}_mwh" for b, a in HEAT_BAND_ACCOUNT.items()}}
    dev = {}
    for a, col in acc.items():
        z = L[L.account == a]; e = annual(n, z.index).groupby(z.country).sum()
        for c in S.index:
            dev[(a, c)] = float(e.get(c, 0.0)) - (float(S.at[c, col]) if col in S.columns else 0.0)
    res["C1_industry_loads_vs_summary_max_abs_mwh"] = max(abs(v) for v in dev.values())
    prof = [l for l in L.index if l in n.loads_t.p_set.columns and L.at[l, "account"] in acc]
    res["C1_profiled_loads"] = len(prof); res["C1_profiled_mean_vs_constant_max_rel"] = max(abs(float(n.loads_t.p_set[l].mean()) / float(L.at[l, "p_set"]) - 1.0) for l in prof) if prof else None
    ind = L[L.account.isin(acc)]; res["C1_365_vs_2920_industry_rel"] = abs(annual(n365, ind.index).sum() / annual(n, ind.index).sum() - 1.0)
    ats = pd.read_csv(od / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False); ats["v"] = pd.to_numeric(ats.value_2050_mwh, errors="coerce").fillna(0.0)
    land = ats[(ats.sector == "Transport") & ats.account.isin(["RoadResidualFuel", "TransportNEC"]) & (ats.carrier != "electricity")].groupby("country").v.sum()
    ev = L[L.account == "LandTransportEV"]; eva = annual(n, ev.index).groupby(ev.country).sum()
    res["C2_ev_vs_land_x_ev_factor_max_rel"] = max(abs(float(eva.get(c, 0.0)) / (float(land[c]) * EV_FACTOR) - 1.0) for c in land.index if land[c] > 0)
    rail = ats[ats.account == "RailNonElectric"].groupby("country").v.sum(); rl = L[L.account == "RailNonElectric"]; rla = annual(n, rl.index).groupby(rl.country).sum()
    res["C2_rail_vs_table_max_abs_mwh"] = max(abs(float(rla.get(c, 0.0)) - float(rail.get(c, 0.0))) for c in set(rail.index) | set(rla.index))
    res["C2_parent_rows_in_table_mwh"] = float(ats[ats.account == "TransportEmbeddedFuelParent"].v.abs().sum())
    pools = n.stores[n.stores.bus.str.startswith("solid biomass")].groupby("country").e_initial.sum()
    led = n.meta["s2_demand_ledger"]["industry"]["biomass_overflow"]
    P = pd.DataFrame([dict(country=c, pool_mwh=float(pools.get(c, 0.0)), fixed_biomass_mwh=float(d["fixed_biomass_after_mwh"]), ratio=(float(d["fixed_biomass_after_mwh"]) / float(pools.get(c, 0.0)) if pools.get(c, 0.0) else None),
                           overflow_mwh=float(d["overflow_industry_mwh"]) + float(d["overflow_agriculture_mwh"]), cap_mwh=float(d["cap_mwh"])) for c, d in led.items()])
    res["C3_pools"] = P.to_dict("records"); res["C3_max_ratio"] = float(P.ratio.dropna().max()); res["C3_VN_slack_share"] = float(1.0 - P[P.country == "VN"].ratio.iloc[0])
    res["C3_pools_at_or_above_0.999"] = P[P.ratio.fillna(0) >= 0.999].country.tolist()
    led1 = n1.meta["s2_demand_ledger"]["industry"]["biomass_overflow"]
    res["C3_pools_at_or_above_0.999_in_D1"] = [c for c, d in led1.items() if float(d["cap_mwh"]) and float(d["fixed_biomass_after_mwh"]) / (float(d["cap_mwh"]) / 0.99) >= 0.999]
    pools1 = n1.stores[n1.stores.bus.str.startswith("solid biomass")].groupby("country").e_initial.sum()
    res["C3_pool_change_vs_D1_twh"] = {c: (float(pools.get(c, 0.0)) - float(pools1.get(c, 0.0))) / 1e6 for c in sorted(set(pools.index) | set(pools1.index)) if abs(float(pools.get(c, 0.0)) - float(pools1.get(c, 0.0))) > 1e-6}
    caps = n.meta.get("external_annual_caps", {}); g = n.generators[n.generators.carrier == "gas production"]
    gc = pd.Series({k: float(caps[k]) for k in g.index if k in caps}).groupby(g.country).sum()
    t = pd.read_csv(R / "research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv").set_index("country").cap_mwh_per_year
    res["C4_gas_caps_vs_table_max_rel"] = max(abs(float(gc.get(c, 0.0)) / float(t[c]) - 1.0) for c in t.index if t[c] > 0)
    res["C4_gas_generators"] = int(len(g)); res["C4_gas_generators_D1"] = int((n1.generators.carrier == "gas production").sum()); res["C4_gas_caps_total_twh"] = float(gc.sum()) / 1e6
    el = L[L.account == "IndustryElectricityRoutes"]; pk = {}
    for c, z in el.groupby("country"):
        ts = sum((n.loads_t.p_set[l] if l in n.loads_t.p_set.columns else pd.Series(float(L.at[l, "p_set"]), index=n.snapshots)) for l in z.index); pk[c] = float(ts.max() / ts.mean())
    res["C5_industry_electricity_peak_over_mean_3h"] = pk
    tz = pd.read_csv(R / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node").utc_offset_h
    res["C5_ID_zones"] = sorted({float(tz[b]) for b in el[el.country == "ID"].bus})
    v4m = n.meta.get("v4_w08", {}); rec = json.loads((od / "V4_SWITCHES.json").read_text())
    res["C6_v4_meta_switch_sha"] = v4m.get("switch_sha256"); res["C6_switch_sha_equals_tables"] = v4m.get("switch_sha256") == rec["switch_sha256"]
    res["C6_switches"] = rec["switches"]; res["C6_tables_dir"] = v4m.get("tables_dir"); res["C6_config_overrides"] = (n.meta.get("research_config") or {}).get("config_overrides")
    res["C6_meoh_per_tco2_in_network"] = (n.meta.get("s3_ammonia_methanol") or n.meta.get("research_ammonia_methanol") or {}).get("parameters") if isinstance(n.meta.get("s3_ammonia_methanol") or n.meta.get("research_ammonia_methanol"), dict) else None
    me = n.links[n.links.carrier == "methanolisation"]
    res["C6_methanolisation_efficiency3"] = sorted(set(round(float(x), 9) for x in me.efficiency3)) if len(me) else None
    res["C6_methanolisation_efficiency3_D1"] = sorted(set(round(float(x), 9) for x in n1.links[n1.links.carrier == "methanolisation"].efficiency3))
    # C10 overflow ledger = table (Fable F-05)
    res["C10_overflow_ledger_vs_table_max_abs_mwh"] = max(abs(float(d["overflow_industry_mwh"]) - float(S.at[c, "biomass_overflow_industry_mwh"])) for c, d in led.items() if c in S.index)
    res["C10_cap_ledger_vs_table_max_abs_mwh"] = max(abs(float(d["cap_mwh"]) - float(S.at[c, "solid_biomass_potential_main_mwh"])) for c, d in led.items() if c in S.index)
    # PHS stock
    su = n.storage_units
    res["PHS_TH2_4_old_group_p_nom"] = float(su.at[PHS_OLD, "p_nom"]) if PHS_OLD in su.index else None
    res["PHS_TH2_4_new_reservoir_p_nom"] = float(su.at[HYD_NEW, "p_nom"]) if HYD_NEW in su.index else None
    res["PHS_existing_by_country_mw"] = su[su.carrier == "PHS existing"].groupby("country").p_nom.sum().to_dict()
    res["PHS_reclass_ledger"] = {k: v for k, v in (n.meta.get("research_phs_stock_reclass") or {}).items() if k != "moved"}
    res["hydro_inflow_TH_annual_twh"] = float(sum((n.storage_units_t.inflow[u] * n.snapshot_weightings.objective).sum() for u in su.index[(su.country == "TH") & (su.carrier == "hydro existing")] if u in n.storage_units_t.inflow.columns)) / 1e6
    res["hydro_inflow_TH_annual_twh_D1"] = float(sum((n1.storage_units_t.inflow[u] * n1.snapshot_weightings.objective).sum() for u in n1.storage_units.index[(n1.storage_units.country == "TH") & (n1.storage_units.carrier == "hydro existing")] if u in n1.storage_units_t.inflow.columns)) / 1e6
    return res


def same(a, b) -> bool:
    if a.dtype.kind in "fc" or b.dtype.kind in "fc":
        x, y = pd.to_numeric(a, errors="coerce"), pd.to_numeric(b, errors="coerce")
        return bool(((x == y) | (x.isna() & y.isna())).all())
    return bool((a.astype(str) == b.astype(str)).all())


def diff(n1, n2) -> dict:
    out = dict(static={}, series={}, sets={})
    for c in n2.iterate_components():
        a = n1.df(c.name); b = c.df
        if set(a.index) != set(b.index):
            out["sets"][c.name] = dict(only_d1=sorted(set(a.index) - set(b.index))[:20], only_d2a=sorted(set(b.index) - set(a.index))[:20])
        idx = a.index.intersection(b.index)
        for col in sorted(set(a.columns) | set(b.columns)):
            if col not in a.columns or col not in b.columns:
                out["static"].setdefault(c.name, {})[col] = "column only in one network"; continue
            x, y = a.loc[idx, col], b.loc[idx, col]
            if not same(x, y):
                bad = [i for i in idx if not same(x.loc[[i]], y.loc[[i]])]
                out["static"].setdefault(c.name, {})[col] = dict(n=len(bad), names=bad[:30], d1=[x.loc[i] for i in bad[:8]], d2a=[y.loc[i] for i in bad[:8]])
        pa, pb = n1.pnl(c.name), c.pnl
        for k in sorted(set(pa) | set(pb)):
            ta, tb = pa.get(k, pd.DataFrame()), pb.get(k, pd.DataFrame()); cols = sorted(set(ta.columns) | set(tb.columns))
            if not cols:
                continue
            if set(ta.columns) != set(tb.columns) or not np.array_equal(ta[cols].to_numpy(), tb.reindex(columns=cols).to_numpy(), equal_nan=True):
                changed = [x for x in cols if x not in ta.columns or x not in tb.columns or not np.array_equal(ta[x].to_numpy(), tb[x].to_numpy(), equal_nan=True)]
                out["series"].setdefault(c.name, {})[k] = dict(n=len(changed), names=changed[:30])
    out["snapshots_and_weightings_equal"] = bool(n1.snapshot_weightings.equals(n2.snapshot_weightings) and n1.snapshots.equals(n2.snapshots))
    mk = sorted(set(n1.meta) | set(n2.meta))
    out["meta_keys_differing"] = [k for k in mk if json.dumps(n1.meta.get(k), sort_keys=True, default=str) != json.dumps(n2.meta.get(k), sort_keys=True, default=str)]
    return out


def classify(d: dict, n1, n2) -> dict:
    """Expected differences of section 3 vs anything else."""
    exp, unexp = [], []
    for comp, cols in d["static"].items():
        for col, v in cols.items():
            names = v["names"] if isinstance(v, dict) else []
            if comp == "Store" and col in ("e_nom", "e_initial") and all(" biomass " in x for x in names):
                exp.append(f"Store.{col} of {len(names)} biomass pools (T04 potential)")
            elif comp == "StorageUnit" and names == [PHS_OLD] and col in ("p_nom", "existing_annual_fixed_om_eur", "source_unit_id", "source_group_capacity_mw", "retained_electric_capacity_mw", "existing_fixed_om_eur_per_mw_year", "marginal_cost", "variable_cost_method"):
                exp.append(f"StorageUnit.{col} of the TH2 4 PHS group (reclassification)")
            elif comp == "Link" and col == "efficiency3" and all(n2.links.at[x, "carrier"] == "methanolisation" for x in names):
                exp.append(f"Link.efficiency3 of {len(names)} methanolisation links (meoh_per_tco2)")
            elif comp == "Link" and col == "efficiency4" and all("methanolisation" in n2.links.at[x, "carrier"] or n2.links.at[x, "carrier"] in ("methanolisation",) or "fuel carbon" in str(n2.links.at[x, "carrier"]) for x in names):
                exp.append(f"Link.efficiency4 of {len(names)} links (fuel-carbon port, meoh_per_tco2)")
            else:
                unexp.append(dict(component=comp, column=col, detail=v if isinstance(v, dict) else str(v)))
    for comp, sers in d["series"].items():
        for k, v in sers.items():
            if comp == "StorageUnit" and k == "inflow" and all(n2.storage_units.at[x, "country"] == "TH" and n2.storage_units.at[x, "carrier"] == "hydro existing" for x in v["names"] if x in n2.storage_units.index):
                exp.append(f"StorageUnit.inflow of {v['n']} TH reservoirs (national inflow re-shared with the reclassified capacity)")
            else:
                unexp.append(dict(component=comp, series=k, detail=v))
    for comp, s in d["sets"].items():
        if comp == "StorageUnit" and s["only_d1"] == [] and s["only_d2a"] == [HYD_NEW]:
            exp.append("new StorageUnit TH2 4 hydro existing::D2A (reclassification)")
        else:
            unexp.append(dict(component=comp, sets=s))
    return dict(expected=exp, unexpected=unexp, passed=(not unexp) and d["snapshots_and_weightings_equal"])


def main():
    out, dres = {}, {}
    for sc, tag in (("integrated", "main_F1"), ("no_new_xb", "main_F2")):
        p = B / sc / f"{sc}_2920_3h_unsolved.nc"; p365 = B / sc / f"{sc}_365_24h_unsolved.nc"
        n = pypsa.Network(str(p)); n365 = pypsa.Network(str(p365)); n1 = pypsa.Network(str(B1 / sc / f"{sc}_2920_3h_unsolved.nc"))
        r = check(tag, n, n365, n1)
        r["network_sha256"] = hashlib.sha256(p.read_bytes()).hexdigest(); r["network_bytes"] = p.stat().st_size; r["network_365_sha256"] = hashlib.sha256(p365.read_bytes()).hexdigest()
        out[tag] = r
        for z, nn in (("2920_3h", n), ("365_24h", None)):
            a = n1 if z == "2920_3h" else pypsa.Network(str(B1 / sc / f"{sc}_365_24h_unsolved.nc")); b = nn if nn is not None else n365
            d = diff(a, b); cl = classify(d, a, b)
            dres[f"{sc}_{z}"] = dict(C8=cl, diff=d)
            print(sc, z, "C8 passed:", cl["passed"], "| expected:", cl["expected"], "| UNEXPECTED:", cl["unexpected"][:5], "| meta keys:", d["meta_keys_differing"])
        print(tag, {k: v for k, v in r.items() if not isinstance(v, (dict, list))})
    (W / "STATIC_CHECKS.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    (W / "evidence").mkdir(exist_ok=True)
    (W / "evidence/D2A_NETWORK_DIFF.json").write_text(json.dumps(dres, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
