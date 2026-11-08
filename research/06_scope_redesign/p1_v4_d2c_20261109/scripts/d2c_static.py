"""V4 D2c section 3 (copy of the D2b scripts/d2b_static.py C1-C6 / C8 / C10-C12, D2c expectations): static checks of the rebuilt v4 main networks (no solver).
Writes STATIC_CHECKS.json and evidence/D2C_NETWORK_DIFF.json into the delivery folder.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/d2c_static.py

  C1 industry electricity / heat loads per country = INDUSTRY_2050_SUMMARY_V4.csv; profiled load means = constants; 365x24h = 2920x3h totals
  C2 EV load = ATS land fuel x the unrounded registry factor; rail = RailNonElectric rows; no parent row
  C3 solid-biomass pools: fixed demand / pool <= 0.99; VN slack >= 1 %; no pool at or above 0.999 that was not there in D2b
  C4 domestic gas caps = GAS_PRODUCTION_CAPS_2050_V4.csv (generator count = D2b)
  C5 curves (peak / mean; ID three time zones)
  C6 v4 identity: n.meta v4_w08 switch SHA = the table folder (biomass_potential v4_adjusted_t06, source_band_basis post_product, lng_regas_adder asean_tariffs)
  C8 network difference D2c vs D2b (2920x3h and 365x24h): every component table and time series value by value, classified into the EXPECTED set registered
     before the build from the change list of section 2 (written in this file before the first build of D2c; instruction section 3: "对 D2b 网络的差异只能是
     五个树干 Store 的潜力（e_nom / e_initial），其余为 UNEXPECTED 即停"):
       (a) Store e_nom / e_initial of the five oil palm trunk pools (T06 basis; every other pool unchanged).
     Anything else (any other static column, any time series, any component set, snapshots / weightings) is listed as UNEXPECTED (stop condition).
     Metadata keys (switch SHA, file hashes, ledgers) are reported, not classified.
  C10 the overflow ledger of the network = INDUSTRY_2050_SUMMARY_V4.csv (Fable F-05); C11 the band shares of the ledger = the table;
  C12 LNG import marginal cost = D2b exactly (no LNG change in D2c).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

sys.path.insert(0, "/home/jin/wt_v4_d2c/scripts_project")
W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_d2c")
B = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d2c/builds/main")
B1 = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d2b/builds/main")
# (D2c: the LNG adder is unchanged; C12 checks equality with D2b)


def annual(n, names) -> pd.Series:
    w = n.snapshot_weightings.objective
    return pd.Series({l: (float((n.loads_t.p_set[l] * w).sum()) if l in n.loads_t.p_set.columns else float(n.loads.at[l, "p_set"]) * float(w.sum())) for l in names}, dtype=float)


def check(tag, n, n365, n1) -> dict:
    from s2_layers import HEAT_BAND_ACCOUNT
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
    res["C3_pools_at_or_above_0.999_in_D2b"] = [c for c, d in led1.items() if float(d["cap_mwh"]) and float(d["fixed_biomass_after_mwh"]) / (float(d["cap_mwh"]) / 0.99) >= 0.999]
    pools1 = n1.stores[n1.stores.bus.str.startswith("solid biomass")].groupby("country").e_initial.sum()
    res["C3_pool_change_vs_D2b_twh"] = {c: (float(pools.get(c, 0.0)) - float(pools1.get(c, 0.0))) / 1e6 for c in sorted(set(pools.index) | set(pools1.index)) if abs(float(pools.get(c, 0.0)) - float(pools1.get(c, 0.0))) > 1e-6}
    tr = n.stores[n.stores.index.str.contains(" biomass oil_palm_trunk")]; tr1 = n1.stores[n1.stores.index.str.contains(" biomass oil_palm_trunk")]
    res["C3_trunk_pools_twh"] = {k: [float(tr1.at[k, "e_nom"]) / 1e6 if k in tr1.index else None, float(tr.at[k, "e_nom"]) / 1e6] for k in tr.index}
    caps = n.meta.get("external_annual_caps", {}); g = n.generators[n.generators.carrier == "gas production"]
    gc = pd.Series({k: float(caps[k]) for k in g.index if k in caps}).groupby(g.country).sum()
    t = pd.read_csv(R / "research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv").set_index("country").cap_mwh_per_year
    res["C4_gas_caps_vs_table_max_rel"] = max(abs(float(gc.get(c, 0.0)) / float(t[c]) - 1.0) for c in t.index if t[c] > 0)
    res["C4_gas_generators"] = int(len(g)); res["C4_gas_generators_D2b"] = int((n1.generators.carrier == "gas production").sum()); res["C4_gas_caps_total_twh"] = float(gc.sum()) / 1e6
    el = L[L.account == "IndustryElectricityRoutes"]; pk = {}
    for c, z in el.groupby("country"):
        ts = sum((n.loads_t.p_set[l] if l in n.loads_t.p_set.columns else pd.Series(float(L.at[l, "p_set"]), index=n.snapshots)) for l in z.index); pk[c] = float(ts.max() / ts.mean())
    res["C5_industry_electricity_peak_over_mean_3h"] = pk
    tz = pd.read_csv(R / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node").utc_offset_h
    res["C5_ID_zones"] = sorted({float(tz[b]) for b in el[el.country == "ID"].bus})
    v4m = n.meta.get("v4_w08", {}); rec = json.loads((od / "V4_SWITCHES.json").read_text())
    res["C6_v4_meta_switch_sha"] = v4m.get("switch_sha256"); res["C6_switch_sha_equals_tables"] = v4m.get("switch_sha256") == rec["switch_sha256"]
    res["C6_switches"] = rec["switches"]; res["C6_tables_dir"] = v4m.get("tables_dir"); res["C6_main_set"] = rec["main_set"]
    res["C6_biomass_potential_file"] = v4m.get("biomass_potential") or (n.meta.get("v4_w08") or {}).get("biomass_potential")
    me = n.links[n.links.carrier == "methanolisation"]
    res["C6_methanolisation_efficiency3"] = sorted(set(round(float(x), 9) for x in me.efficiency3)) if len(me) else None
    # C10 / C11 overflow ledger and band shares = table
    res["C10_overflow_ledger_vs_table_max_abs_mwh"] = max(abs(float(d["overflow_industry_mwh"]) - float(S.at[c, "biomass_overflow_industry_mwh"])) for c, d in led.items() if c in S.index)
    res["C10_cap_ledger_vs_table_max_abs_mwh"] = max(abs(float(d["cap_mwh"]) - float(S.at[c, "solid_biomass_potential_main_mwh"])) for c, d in led.items() if c in S.index)
    c11 = {}
    for c, d in led.items():
        sh = d.get("source_band_shares")
        if sh and c in S.index:
            c11[c] = max(abs(float(sh[b]) - float(S.at[c, f"biomass_source_band_{b}_share"])) for b in sh)
    res["C11_band_shares_ledger_vs_table_max_abs"] = max(c11.values()) if c11 else 0.0
    res["C11_overflow_useful_heat_mwh"] = {c: d.get("useful_heat_mwh") for c, d in led.items() if float(d["overflow_industry_mwh"]) > 0}
    res["C11_overflow_useful_heat_mwh_D2b"] = {c: d.get("useful_heat_mwh") for c, d in led1.items() if float(d["overflow_industry_mwh"]) > 0}
    # C12 LNG adder (D2c: no LNG change; the marginal cost must equal the D2b network exactly)
    lng = n.generators[n.generators.carrier == "LNG import"]; lng1 = n1.generators[n1.generators.carrier == "LNG import"]
    common = lng.index.intersection(lng1.index)
    d_mc = (lng.loc[common, "marginal_cost"].astype(float) - lng1.loc[common, "marginal_cost"].astype(float))
    res["C12_lng_generators"] = int(len(lng)); res["C12_lng_generators_D2b"] = int(len(lng1))
    res["C12_lng_mc_change_min_max"] = [float(d_mc.min()), float(d_mc.max())] if len(d_mc) else None
    res["C12_lng_mc_change_expected"] = 0.0
    res["C12_lng_mc_change_max_dev"] = float(d_mc.abs().max()) if len(d_mc) else None
    res["C12_lng_ledger"] = {k: v for k, v in ((n.meta.get("s3_gas_ledger") or n.meta.get("research_gas") or {}).get("lng") or {}).items() if k in ("regasification_adder", "adder_status")} if isinstance(n.meta.get("s3_gas_ledger") or n.meta.get("research_gas"), dict) else None
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
            out["sets"][c.name] = dict(only_d2b=sorted(set(a.index) - set(b.index))[:20], only_d2c=sorted(set(b.index) - set(a.index))[:20])
        idx = a.index.intersection(b.index)
        for col in sorted(set(a.columns) | set(b.columns)):
            if col not in a.columns or col not in b.columns:
                out["static"].setdefault(c.name, {})[col] = "column only in one network"; continue
            x, y = a.loc[idx, col], b.loc[idx, col]
            if not same(x, y):
                bad = [i for i in idx if not same(x.loc[[i]], y.loc[[i]])]
                out["static"].setdefault(c.name, {})[col] = dict(n=len(bad), names=bad[:40], d2b=[x.loc[i] for i in bad[:8]], d2c=[y.loc[i] for i in bad[:8]], all_names=bad)
        pa, pb = n1.pnl(c.name), c.pnl
        for k in sorted(set(pa) | set(pb)):
            ta, tb = pa.get(k, pd.DataFrame()), pb.get(k, pd.DataFrame()); cols = sorted(set(ta.columns) | set(tb.columns))
            if not cols:
                continue
            if set(ta.columns) != set(tb.columns) or not np.array_equal(ta[cols].to_numpy(), tb.reindex(columns=cols).to_numpy(), equal_nan=True):
                changed = [x for x in cols if x not in ta.columns or x not in tb.columns or not np.array_equal(ta[x].to_numpy(), tb[x].to_numpy(), equal_nan=True)]
                out["series"].setdefault(c.name, {})[k] = dict(n=len(changed), names=changed[:40], all_names=changed)
    out["snapshots_and_weightings_equal"] = bool(n1.snapshot_weightings.equals(n2.snapshot_weightings) and n1.snapshots.equals(n2.snapshots))
    mk = sorted(set(n1.meta) | set(n2.meta))
    out["meta_keys_differing"] = [k for k in mk if json.dumps(n1.meta.get(k), sort_keys=True, default=str) != json.dumps(n2.meta.get(k), sort_keys=True, default=str)]
    return out


def classify(d: dict, n1, n2) -> dict:
    """The expected difference registered in the docstring (a) - the e_nom / e_initial of the five oil palm trunk pools - vs anything else."""
    exp, unexp, trunk = [], [], {}
    for comp, cols in d["static"].items():
        for col, v in cols.items():
            names = v["all_names"] if isinstance(v, dict) else []
            if comp == "Store" and col in ("e_nom", "e_initial") and names and all(" biomass oil_palm_trunk" in x for x in names):
                exp.append(f"(a) Store.{col} of {len(names)} oil palm trunk pools (T06 basis): {sorted(names)}")
                trunk[col] = sorted(names)
            else:
                unexp.append(dict(component=comp, column=col, detail={k: v[k] for k in v if k != "all_names"} if isinstance(v, dict) else str(v)))
    all_trunk = sorted(x for x in n2.stores.index if " biomass oil_palm_trunk" in x)
    if trunk.get("e_nom") != all_trunk or trunk.get("e_initial") != all_trunk or len(all_trunk) != 5:   # the five trunk pools must all change, in both columns
        unexp.append(dict(component="Store", column="e_nom / e_initial", detail=f"trunk pools changed {trunk} vs the network's trunk pools {all_trunk}"))
    for comp, sers in d["series"].items():
        for k, v in sers.items():
            unexp.append(dict(component=comp, series=k, detail={kk: vv for kk, vv in v.items() if kk != "all_names"}))
    for comp, s in d["sets"].items():
        unexp.append(dict(component=comp, sets=s))
    for comp, cols in d["static"].items():   # strip the full name lists before the JSON dump
        for col, v in cols.items():
            if isinstance(v, dict):
                v.pop("all_names", None)
    for comp, sers in d["series"].items():
        for k, v in sers.items():
            v.pop("all_names", None)
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
    (W / "evidence/D2C_NETWORK_DIFF.json").write_text(json.dumps(dres, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
