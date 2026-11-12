"""X20 §3 第 4 步（不求解）：把 W14 的全部静态核对（work/p1_v4_w14_20261109/scripts/w14_static.py 的 C1-C6、C6b、C9-C12，函数逐字抄入、只改路径与对照网络）
用在 v5 主集 F1 / F2 网络上；对照网络 n1 = v5off（= W14 数据，evidence/V5OFF_VS_W14_*.json 已逐值证明），所以 C3 / C4 / C12 中与 n1 的差别就是 v5 的改动。
另加 C6v5：用构建记录的覆盖项重新组装配置（m08a_variants.composed_config），v5_common.check_network_meta_v5 与 B12 恒等式。
T56：按 s2_solve.py --truncate 56 规则（前 56 个时段 + set_representative_weights）切出 v5 主集与 v5off 的 56 时段网络，导出到 $D/trunc56/（PYTHONHASHSEED=0），记录 SHA256，
并在切后网络上重做与时段无关的核对。
用法：PYTHONHASHSEED=0 python 68_static_w14.py   输出 evidence/V5_STATIC_W14CHECKS.json、evidence/V5_TRUNC56.json"""
from __future__ import annotations

import gc
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

R = Path("/home/jin/wt_v5_x20")
sys.path.insert(0, str(R / "scripts_project"))
W = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
import os   # noqa: E402
MAIN, OFF, TAG = os.environ.get("X20_MAIN", "v5main"), os.environ.get("X20_OFF", "v5off"), os.environ.get("X20_TAG", "")   # C segment: c2main / c2off / _C2
B = W / "builds" / MAIN; B1 = W / "builds" / OFF; T56 = W / "trunc56"
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
    """snapshot-independent checks (C3, C4, C6, C10-C12 of d2c_static.py; n1 = the v5off network of the same scenario)"""
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
    res["C3_pools_at_or_above_0.999_in_v5off"] = [c for c, d in led1.items() if float(d["cap_mwh"]) and float(d["fixed_biomass_after_mwh"]) / (float(d["cap_mwh"]) / 0.99) >= 0.999]
    res["C3_no_new_zero_margin_pool"] = set(res["C3_pools_at_or_above_0.999"]) <= set(res["C3_pools_at_or_above_0.999_in_v5off"])
    res["C3_ratio_le_0.99"] = bool(P.ratio.dropna().max() <= 0.99 + 1e-9)
    res["C3_VN_slack_ge_1pct"] = res["C3_VN_slack_share"] >= 0.01 - 1e-12
    caps = n.meta.get("external_annual_caps", {}); g = n.generators[n.generators.carrier == "gas production"]
    gc_ = pd.Series({k: float(caps[k]) for k in g.index if k in caps}).groupby(g.country).sum()
    t = pd.read_csv(R / "research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv").set_index("country").cap_mwh_per_year
    res["C4_gas_caps_vs_v4_table_by_country"] = {c: dict(network_twh=round(float(gc_.get(c, 0.0)) / 1e6, 4), v4_table_twh=round(float(t[c]) / 1e6, 4)) for c in t.index}
    res["C4_gas_caps_vs_table_max_rel"] = max(abs(float(gc_.get(c, 0.0)) / float(t[c]) - 1.0) for c in t.index if t[c] > 0)
    res["C4_gas_generators"] = int(len(g)); res["C4_gas_generators_v5off"] = int((n1.generators.carrier == "gas production").sum()); res["C4_gas_caps_total_twh"] = float(gc_.sum()) / 1e6
    res["C4_v5_gas_cap_rule"] = (n.meta.get("research_gas_network") or {}).get("v5_gas_cap_rule")
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
    res["C12_lng_generators"] = int(len(lng)); res["C12_lng_generators_v5off"] = int(len(lng1))
    res["C12_lng_mc_change_max_dev_vs_v5off"] = float(d_mc.abs().max()) if len(d_mc) else None
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
    res["C2_ev_loads_by_carrier"] = ev.carrier.value_counts().to_dict()
    rail = ats[ats.account == "RailNonElectric"].groupby("country").v.sum(); rl = L[L.account == "RailNonElectric"]; rla = annual(n, rl.index).groupby(rl.country).sum()
    res["C2_rail_vs_table_max_abs_mwh"] = max(abs(float(rla.get(c, 0.0)) - float(rail.get(c, 0.0))) for c in set(rail.index) | set(rla.index))
    res["C2_parent_rows_in_table_mwh"] = float(ats[ats.account == "TransportEmbeddedFuelParent"].v.abs().sum())
    el = L[L.account == "IndustryElectricityRoutes"]; pk = {}
    for c, z in el.groupby("country"):
        ts = sum((n.loads_t.p_set[l] if l in n.loads_t.p_set.columns else pd.Series(float(L.at[l, "p_set"]), index=n.snapshots)) for l in z.index); pk[c] = float(ts.max() / ts.mean())
    res["C5_industry_electricity_peak_over_mean_3h"] = pk
    tz = pd.read_csv(R / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node").utc_offset_h
    node = el.bus.astype(str).str.replace(" low voltage", "", regex=False)   # V5 X20 (3-4): industry electricity sits on '<node> low voltage' (PyPSA-Eur rule)
    res["C5_industry_electricity_on_lv_bus"] = int(el.bus.astype(str).str.endswith(" low voltage").sum())
    res["C5_ID_zones"] = sorted({float(tz[b]) for b in node[el.country == "ID"] if b in tz.index})
    res["C5_nodes_without_timezone"] = sorted({b for b in node if b not in tz.index})
    res.update(check_static(n, n1))
    return res


def meta_check(n) -> dict:
    """C6b + C6v5: check_network_meta (v4) and check_network_meta_v5 with the configuration composed from the configuration files + the overrides recorded in
    the network, and the B12 identity"""
    from m08a_variants import composed_config
    from scenario_network import config_sha
    from v4_common import check_network_meta
    from v5_common import check_network_meta_v5
    ov = list((n.meta.get("research_config") or {}).get("config_overrides") or [])
    cfg = composed_config(R, str(n.meta.get("scenario")), ov)
    want = config_sha(cfg["research"])
    out = dict(overrides=ov, research_config_sha256_network=n.meta.get("research_config_sha256"), research_config_sha256_composed=want, b12_identity=n.meta.get("research_config_sha256") == want)
    for k, f in (("check_network_meta_v4", lambda: check_network_meta(n.meta, cfg, R)), ("check_network_meta_v5", lambda: check_network_meta_v5(n.meta, cfg))):
        try:
            out[k] = f(); out[k + "_error"] = None
        except Exception as e:   # noqa: BLE001 - reported, the check fails
            out[k] = None; out[k + "_error"] = str(e)
    out["passed"] = bool(out["b12_identity"] and out["check_network_meta_v4"] and out["check_network_meta_v4"].get("enabled") and out["check_network_meta_v5"]
                         and out["check_network_meta_v5"].get("enabled") and out["check_network_meta_v5"].get("main_set"))
    return out


def cut56(src: Path, dst: Path) -> dict:
    """the s2_solve.py --truncate 56 rule: n.set_snapshots(n.snapshots[:56]) + set_representative_weights(n); exported deterministically"""
    from s2_solve import set_representative_weights
    n = pypsa.Network(str(src)); n.set_snapshots(n.snapshots[:56]); sc = set_representative_weights(n)
    dst.parent.mkdir(parents=True, exist_ok=True); n.export_to_netcdf(dst)
    return dict(source=str(src), source_sha256=sha(src), file=str(dst), sha256=sha(dst), bytes=dst.stat().st_size, scaling=sc)


def main():
    out, t56 = {}, {}
    for sc, tag in (("integrated", "F1"), ("no_new_xb", "F2")):
        p = B / sc / f"{sc}_2920_3h_unsolved.nc"; p365 = B / sc / f"{sc}_365_24h_unsolved.nc"; q = B1 / sc / f"{sc}_2920_3h_unsolved.nc"
        n = pypsa.Network(str(p)); n365 = pypsa.Network(str(p365)); n1 = pypsa.Network(str(q))
        r = check(n, n365, n1); r["C6v5_meta"] = meta_check(n); r["network_sha256"] = sha(p); r["v5off_sha256"] = sha(q)
        out[tag] = r
        print(tag, "C1", r["C1_industry_loads_vs_summary_max_abs_mwh"], "C2", r["C2_ev_vs_land_x_ev_factor_max_rel"], "C3", r["C3_max_ratio"], r["C3_no_new_zero_margin_pool"],
              "C4", r["C4_gas_caps_total_twh"], r["C4_gas_generators"], "C6v5", r["C6v5_meta"]["passed"], "C9", r["C9_trunk_at_proxy"], "C12", r["C12_lng_mc_change_max_dev_vs_v5off"], flush=True)
        del n365, n1; gc.collect()
        cw = cut56(p, T56 / f"{MAIN}_{sc}_56.nc"); co = cut56(q, T56 / f"{OFF}_{sc}_56.nc")
        a56 = pypsa.Network(cw["file"]); o56 = pypsa.Network(co["file"])
        w = a56.snapshot_weightings
        pools_unscaled = bool(np.array_equal(a56.stores.e_initial.to_numpy(), n.stores.e_initial.to_numpy()) and np.array_equal(a56.stores.e_nom.to_numpy(), n.stores.e_nom.to_numpy()))
        s56 = check_static(a56, o56); s56["C6v5_meta"] = meta_check(a56)
        t56[tag] = dict(v5main=cw, v5off=co, snapshots=int(len(a56.snapshots)), first=str(a56.snapshots[0]), last=str(a56.snapshots[-1]),
                        weights_all_8760_over_56=bool(np.allclose(w.to_numpy(), 8760.0 / 56, rtol=0, atol=1e-12)), weight_sum=float(w.objective.sum()),
                        pools_unscaled_vs_2920=pools_unscaled, static_checks=s56)
        print(tag, "T56", cw["sha256"][:12], "v5off", co["sha256"][:12], "weights", t56[tag]["weights_all_8760_over_56"], "pools unscaled", pools_unscaled, "C6v5", s56["C6v5_meta"]["passed"], flush=True)
        del a56, o56, n; gc.collect()
    (W / f"evidence/V5_STATIC_W14CHECKS{TAG}.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    (W / f"evidence/V5_TRUNC56{TAG}.json").write_text(json.dumps(t56, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
