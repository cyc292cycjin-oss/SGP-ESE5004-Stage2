"""V4 W14 section 2.2-2.3: every static check of the W08 / D1 / D2a / D2b / D2c steps on the v4 main networks of the HPC package (2920x3h and the
56-snapshot networks cut by the same rule), and the comparison with the D2c smoke networks. No solver, no LP of the 2920x3h networks.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w14_static.py

Networks: W14 build results_project/v4w14/builds/main (build commit of BATCH_DEF.json), D2c build results_project/v4d2c/builds/main (the D2c smoke networks
db33f84e / f03aab19), v3.1 package networks work/p1_v3_20261102/hpc_package_v3_1/networks (structure comparison C7).
  C1-C6, C10-C12  the D2c checks (scripts of p1_v4_d2c_20261109/scripts/d2c_static.py, copied below; D2c is the previous step: C3 no new pool >= 0.999 vs D2c,
                  C4 generator count = D2c, C12 LNG marginal cost = D2c)
  C6b             D1 check (decision 214 item 8; v4_common.check_network_meta, also in the package preflight): switch SHA256 of the network meta = table folder
                  V4_SWITCHES.json = configuration composed from the configuration files and the overrides recorded in the network; and B12 identity:
                  research_config_sha256 of the network = hash of that composed configuration
  C7              W08 / D1: structure vs v3.1 (component sets; listed, explained by the W08-D2c change lists)
  C8              difference W14 vs D2c, 2920x3h and 365x24h, every component table and time series value by value: EXPECTED = no difference at all (same
                  code, inputs and configuration; only n.meta may differ by the build-worktree path of the geothermal bus mapping source and the base-network
                  SHA256 of the variant that follows from it - every differing meta leaf is listed)
  C9              D1: the five trunk Stores carry the registry proxy biomass_missing_cost_proxy; the biomass ledger records the rule
  T56             the 56-snapshot networks: the s2_solve.py --truncate 56 rule (first 56 snapshots, set_representative_weights: weights 8760 / 56, annual quantities
                  unscaled) applied to the W14 and to the D2c networks, exported (PYTHONHASHSEED=0) to results_project/v4w14/trunc56; SHA256 of both and the
                  component comparison (= section 2.3: identical -> the HPC smoke expectation is the D2c smoke objective); the snapshot-independent checks
                  C3 / C4 / C6 / C6b / C9 / C10-C12 on the cut network
  zero-slack gate and "no new zero-margin row": scripts_project/zero_slack_check.py, run separately (scripts/w14_zero_slack.sh) on all four networks
Writes STATIC_CHECKS.json, evidence/W14_NETWORK_DIFF.json, evidence/W14_TRUNC56.json.
"""
from __future__ import annotations

import gc
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

R = Path("/home/jin/wt_v4_w14")
sys.path.insert(0, str(R / "scripts_project"))
W = Path(__file__).resolve().parents[1]
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
B = MAIN / "v4w14/builds/main"
B1 = MAIN / "v4d2c/builds/main"
PKG31 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks")
T56 = MAIN / "v4w14/trunc56"
TRUNK = sorted(f"{c} biomass oil_palm_trunk" for c in ("ID", "KH", "MY", "PH", "TH"))


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def annual(n, names) -> pd.Series:
    w = n.snapshot_weightings.objective
    return pd.Series({l: (float((n.loads_t.p_set[l] * w).sum()) if l in n.loads_t.p_set.columns else float(n.loads.at[l, "p_set"]) * float(w.sum())) for l in names}, dtype=float)


def check_static(n, n1) -> dict:
    """snapshot-independent checks (C3, C4, C6, C10-C12 of d2c_static.py; n1 = the D2c network of the same scenario)"""
    od = R / n.meta["v4_w08"]["tables_dir"]
    S = pd.read_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
    res = {}
    pools = n.stores[n.stores.bus.str.startswith("solid biomass")].groupby("country").e_initial.sum()
    led = n.meta["s2_demand_ledger"]["industry"]["biomass_overflow"]
    P = pd.DataFrame([dict(country=c, pool_mwh=float(pools.get(c, 0.0)), fixed_biomass_mwh=float(d["fixed_biomass_after_mwh"]), ratio=(float(d["fixed_biomass_after_mwh"]) / float(pools.get(c, 0.0)) if pools.get(c, 0.0) else None),
                           overflow_mwh=float(d["overflow_industry_mwh"]) + float(d["overflow_agriculture_mwh"]), cap_mwh=float(d["cap_mwh"])) for c, d in led.items()])
    res["C3_pools"] = P.to_dict("records"); res["C3_max_ratio"] = float(P.ratio.dropna().max()); res["C3_VN_slack_share"] = float(1.0 - P[P.country == "VN"].ratio.iloc[0])
    res["C3_pools_at_or_above_0.999"] = P[P.ratio.fillna(0) >= 0.999].country.tolist()
    led1 = n1.meta["s2_demand_ledger"]["industry"]["biomass_overflow"]
    res["C3_pools_at_or_above_0.999_in_D2c"] = [c for c, d in led1.items() if float(d["cap_mwh"]) and float(d["fixed_biomass_after_mwh"]) / (float(d["cap_mwh"]) / 0.99) >= 0.999]
    res["C3_no_new_zero_margin_pool"] = set(res["C3_pools_at_or_above_0.999"]) <= set(res["C3_pools_at_or_above_0.999_in_D2c"])
    res["C3_ratio_le_0.99"] = bool(P.ratio.dropna().max() <= 0.99 + 1e-9)
    res["C3_VN_slack_ge_1pct"] = res["C3_VN_slack_share"] >= 0.01 - 1e-12
    caps = n.meta.get("external_annual_caps", {}); g = n.generators[n.generators.carrier == "gas production"]
    gc_ = pd.Series({k: float(caps[k]) for k in g.index if k in caps}).groupby(g.country).sum()
    t = pd.read_csv(R / "research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv").set_index("country").cap_mwh_per_year
    res["C4_gas_caps_vs_table_max_rel"] = max(abs(float(gc_.get(c, 0.0)) / float(t[c]) - 1.0) for c in t.index if t[c] > 0)
    res["C4_gas_generators"] = int(len(g)); res["C4_gas_generators_D2c"] = int((n1.generators.carrier == "gas production").sum()); res["C4_gas_caps_total_twh"] = float(gc_.sum()) / 1e6
    v4m = n.meta.get("v4_w08", {}); rec = json.loads((od / "V4_SWITCHES.json").read_text())
    res["C6_v4_meta_switch_sha"] = v4m.get("switch_sha256"); res["C6_switch_sha_equals_tables"] = v4m.get("switch_sha256") == rec["switch_sha256"]
    res["C6_switches"] = rec["switches"]; res["C6_tables_dir"] = v4m.get("tables_dir"); res["C6_main_set"] = rec["main_set"]
    me = n.links[n.links.carrier == "methanolisation"]
    res["C6_methanolisation_efficiency3"] = sorted(set(round(float(x), 9) for x in me.efficiency3)) if len(me) else None
    res["C10_overflow_ledger_vs_table_max_abs_mwh"] = max(abs(float(d["overflow_industry_mwh"]) - float(S.at[c, "biomass_overflow_industry_mwh"])) for c, d in led.items() if c in S.index)
    res["C10_cap_ledger_vs_table_max_abs_mwh"] = max(abs(float(d["cap_mwh"]) - float(S.at[c, "solid_biomass_potential_main_mwh"])) for c, d in led.items() if c in S.index)
    c11 = {}
    for c, d in led.items():
        sh = d.get("source_band_shares")
        if sh and c in S.index:
            c11[c] = max(abs(float(sh[b]) - float(S.at[c, f"biomass_source_band_{b}_share"])) for b in sh)
    res["C11_band_shares_ledger_vs_table_max_abs"] = max(c11.values()) if c11 else 0.0
    lng = n.generators[n.generators.carrier == "LNG import"]; lng1 = n1.generators[n1.generators.carrier == "LNG import"]
    common = lng.index.intersection(lng1.index)
    d_mc = (lng.loc[common, "marginal_cost"].astype(float) - lng1.loc[common, "marginal_cost"].astype(float))
    res["C12_lng_generators"] = int(len(lng)); res["C12_lng_generators_D2c"] = int(len(lng1))
    res["C12_lng_mc_change_max_dev_vs_D2c"] = float(d_mc.abs().max()) if len(d_mc) else None
    # C9 (D1): trunk Stores at the registry proxy, ledger rule
    reg = pd.read_csv(R / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    proxy = float(reg.at["biomass_missing_cost_proxy", "value"])
    mcl = (n.meta.get("research_biomass") or {}).get("missing_cost_rule") or {}
    res["C9_proxy_eur_per_mwh"] = proxy
    res["C9_trunk_at_proxy"] = bool((n.stores.loc[TRUNK, "marginal_cost"].astype(float) == proxy).all())
    res["C9_ledger_rule"] = mcl.get("rule"); res["C9_ledger_stores"] = sorted(x["store"] for x in mcl.get("stores", []))
    return res


def check(n, n365, n1) -> dict:
    """C1, C2, C5 (time-series checks of d2c_static.py) + check_static"""
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
    el = L[L.account == "IndustryElectricityRoutes"]; pk = {}
    for c, z in el.groupby("country"):
        ts = sum((n.loads_t.p_set[l] if l in n.loads_t.p_set.columns else pd.Series(float(L.at[l, "p_set"]), index=n.snapshots)) for l in z.index); pk[c] = float(ts.max() / ts.mean())
    res["C5_industry_electricity_peak_over_mean_3h"] = pk
    tz = pd.read_csv(R / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node").utc_offset_h
    res["C5_ID_zones"] = sorted({float(tz[b]) for b in el[el.country == "ID"].bus})
    res.update(check_static(n, n1))
    return res


def meta_check(n) -> dict:
    """C6b: D1 check_network_meta with the configuration composed from the configuration files + the overrides recorded in the network, and the B12 identity"""
    from m08a_variants import composed_config
    from scenario_network import config_sha
    from v4_common import check_network_meta
    ov = list((n.meta.get("research_config") or {}).get("config_overrides") or [])
    cfg = composed_config(R, str(n.meta.get("scenario")), ov)
    want = config_sha(cfg["research"])
    try:
        r = check_network_meta(n.meta, cfg, R); err = None
    except Exception as e:   # noqa: BLE001 - reported, the check fails
        r, err = None, str(e)
    return dict(overrides=ov, check_network_meta=r, error=err, passed=(err is None and bool(r) and r.get("enabled") and r.get("main_set")),
                research_config_sha256_network=n.meta.get("research_config_sha256"), research_config_sha256_composed=want, b12_identity=n.meta.get("research_config_sha256") == want)


def same(a, b) -> bool:
    if a.dtype.kind in "fc" or b.dtype.kind in "fc":
        x, y = pd.to_numeric(a, errors="coerce"), pd.to_numeric(b, errors="coerce")
        return bool(((x == y) | (x.isna() & y.isna())).all())
    return bool((a.astype(str) == b.astype(str)).all())


def leaf_diff(a, b, path="", out=None, limit=60):
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            leaf_diff(a.get(k), b.get(k), f"{path}/{k}", out, limit)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            leaf_diff(x, y, f"{path}[{i}]", out, limit)
    elif json.dumps(a, sort_keys=True, default=str) != json.dumps(b, sort_keys=True, default=str):
        out.append(dict(path=path, d2c=str(a)[:200], w14=str(b)[:200]))
    return out


def diff(n1, n2) -> dict:
    out = dict(static={}, series={}, sets={})
    for c in n2.iterate_components():
        a = n1.df(c.name); b = c.df
        if set(a.index) != set(b.index):
            out["sets"][c.name] = dict(only_d2c=sorted(set(a.index) - set(b.index))[:20], only_w14=sorted(set(b.index) - set(a.index))[:20])
        idx = a.index.intersection(b.index)
        for col in sorted(set(a.columns) | set(b.columns)):
            if col not in a.columns or col not in b.columns:
                out["static"].setdefault(c.name, {})[col] = "column only in one network"; continue
            if not same(a.loc[idx, col], b.loc[idx, col]):
                bad = [i for i in idx if not same(a.loc[[i], col], b.loc[[i], col])]
                out["static"].setdefault(c.name, {})[col] = dict(n=len(bad), names=bad[:20])
        pa, pb = n1.pnl(c.name), c.pnl
        for k in sorted(set(pa) | set(pb)):
            ta, tb = pa.get(k, pd.DataFrame()), pb.get(k, pd.DataFrame()); cols = sorted(set(ta.columns) | set(tb.columns))
            if not cols:
                continue
            if set(ta.columns) != set(tb.columns) or not np.array_equal(ta[cols].to_numpy(), tb.reindex(columns=cols).to_numpy(), equal_nan=True):
                changed = [x for x in cols if x not in ta.columns or x not in tb.columns or not np.array_equal(ta[x].to_numpy(), tb[x].to_numpy(), equal_nan=True)]
                out["series"].setdefault(c.name, {})[k] = dict(n=len(changed), names=changed[:20])
    out["snapshots_and_weightings_equal"] = bool(n1.snapshot_weightings.equals(n2.snapshot_weightings) and n1.snapshots.equals(n2.snapshots))
    mk = sorted(set(n1.meta) | set(n2.meta))
    out["meta_keys_differing"] = [k for k in mk if json.dumps(n1.meta.get(k), sort_keys=True, default=str) != json.dumps(n2.meta.get(k), sort_keys=True, default=str)]
    out["meta_leaves_differing"] = {k: leaf_diff(n1.meta.get(k), n2.meta.get(k)) for k in out["meta_keys_differing"]}
    out["identical_data"] = (not out["static"]) and (not out["series"]) and (not out["sets"]) and out["snapshots_and_weightings_equal"]
    return out


def structure(a, b) -> dict:
    out = {}
    for c in ("buses", "links", "generators", "stores", "lines", "storage_units", "loads"):
        A, Bb = set(getattr(a, c).index), set(getattr(b, c).index)
        out[c] = dict(n_v31=len(A), n_v4=len(Bb), n_only_v31=len(A - Bb), n_only_v4=len(Bb - A), only_v31=sorted(A - Bb)[:30], only_v4=sorted(Bb - A)[:30])
    return out


def cut56(src: Path, dst: Path) -> dict:
    """the s2_solve.py --truncate 56 rule: n.set_snapshots(n.snapshots[:56]) + set_representative_weights(n); exported deterministically"""
    from s2_solve import set_representative_weights
    n = pypsa.Network(str(src)); n.set_snapshots(n.snapshots[:56]); sc = set_representative_weights(n)
    dst.parent.mkdir(parents=True, exist_ok=True); n.export_to_netcdf(dst)
    return dict(source=str(src), source_sha256=sha(src), file=str(dst), sha256=sha(dst), bytes=dst.stat().st_size, scaling=sc)


def main():
    out, dres, t56 = {}, {}, {}
    for sc, tag in (("integrated", "F1"), ("no_new_xb", "F2")):
        p = B / sc / f"{sc}_2920_3h_unsolved.nc"; p365 = B / sc / f"{sc}_365_24h_unsolved.nc"; q = B1 / sc / f"{sc}_2920_3h_unsolved.nc"
        n = pypsa.Network(str(p)); n365 = pypsa.Network(str(p365)); n1 = pypsa.Network(str(q))
        r = check(n, n365, n1)
        r["C6b_meta"] = meta_check(n)
        r["network_sha256"] = sha(p); r["network_bytes"] = p.stat().st_size; r["network_365_sha256"] = sha(p365)
        r["network_meta_v4"] = dict(switch_sha256=n.meta["v4_w08"].get("switch_sha256"), tables_dir=n.meta["v4_w08"].get("tables_dir"))
        r["d2c_network_sha256"] = sha(q)
        v31 = pypsa.Network(str(PKG31 / f"{sc}_2920_3h_unsolved.nc"))
        r["C7_structure_vs_v31"] = structure(v31, n); del v31; gc.collect()
        d = diff(n1, n); dres[f"{sc}_2920_3h"] = d
        print(tag, "2920 C8 identical data:", d["identical_data"], "| meta keys:", d["meta_keys_differing"], flush=True)
        del n1, n365; gc.collect()
        m1 = pypsa.Network(str(B1 / sc / f"{sc}_365_24h_unsolved.nc")); m = pypsa.Network(str(p365))
        d = diff(m1, m); dres[f"{sc}_365_24h"] = d; del m1, m; gc.collect()
        print(tag, "365 C8 identical data:", d["identical_data"], "| meta keys:", d["meta_keys_differing"], flush=True)
        r["C8_identical_data_2920"] = dres[f"{sc}_2920_3h"]["identical_data"]; r["C8_identical_data_365"] = dres[f"{sc}_365_24h"]["identical_data"]
        out[tag] = r
        print(tag, {k: v for k, v in r.items() if not isinstance(v, (dict, list))}, flush=True)
        # T56: the same cut of the W14 and of the D2c network; component comparison and the snapshot-independent checks on the cut W14 network
        cw = cut56(p, T56 / f"w14_{sc}_56.nc"); cd = cut56(q, T56 / f"d2c_{sc}_56.nc")
        a56 = pypsa.Network(cw["file"]); b56 = pypsa.Network(cd["file"])
        d56 = diff(b56, a56)
        n1 = pypsa.Network(str(q))
        s56 = check_static(a56, n1); s56["C6b_meta"] = meta_check(a56)
        w = a56.snapshot_weightings
        pools_unscaled = bool(np.array_equal(a56.stores.e_initial.to_numpy(), n.stores.e_initial.to_numpy()) and np.array_equal(a56.stores.e_nom.to_numpy(), n.stores.e_nom.to_numpy()))
        t56[tag] = dict(w14=cw, d2c=cd, sha256_equal=cw["sha256"] == cd["sha256"], identical_data=d56["identical_data"], meta_keys_differing=d56["meta_keys_differing"],
                        meta_leaves_differing=d56["meta_leaves_differing"], snapshots=int(len(a56.snapshots)), first=str(a56.snapshots[0]), last=str(a56.snapshots[-1]),
                        weights_all_8760_over_56=bool(np.allclose(w.to_numpy(), 8760.0 / 56, rtol=0, atol=1e-12)), weight_sum=float(w.objective.sum()),
                        pools_unscaled_vs_2920=pools_unscaled, static_checks=s56, static_diff=d56["static"], series_diff=d56["series"], sets_diff=d56["sets"])
        print(tag, "T56: sha equal", t56[tag]["sha256_equal"], "identical data", d56["identical_data"], "meta", d56["meta_keys_differing"], "weights", t56[tag]["weights_all_8760_over_56"], flush=True)
        del a56, b56, n1, n; gc.collect()
    (W / "STATIC_CHECKS.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    (W / "evidence").mkdir(exist_ok=True)
    (W / "evidence/W14_NETWORK_DIFF.json").write_text(json.dumps(dres, indent=1, default=str) + "\n")
    (W / "evidence/W14_TRUNC56.json").write_text(json.dumps(t56, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
