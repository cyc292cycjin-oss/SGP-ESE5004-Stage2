"""X20 §3 第 4 步（不求解）：v5 主集 F1 / F2 2920x3h 网络的 v5 专项静态核对，与 v5off（= W14 数据）逐项对照；输出 evidence/V5_STATIC_CHECKS.json 与 evidence/V5_COMPONENT_DELTA.csv。
  S1 开关：v5_x20 记录的开关 SHA = v5 主集；v4 表目录 = out_ras_v5；v4_common.check_network_meta / v5_common.check_network_meta_v5 用网络内 research_config 复核；B12：research_config_sha256 = 其哈希
  S2 默认值：baseline.yaml 中 v5.enabled = false、列出的值 = V5_MAIN；v5off 网络与 W14 数据逐值相同（evidence/V5OFF_VS_W14_*.json）
  S3 输入总量：各 v5 层账本（存量、地热、PH 直流、AC 去重、气上限、水电入流、配电网、专用状态、剖面选择）
  S4 组件差异：按组件类型与 carrier 计数、容量合计（v5main - v5off）
用法：python x20_static.py"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

WT = Path("/home/jin/wt_v5_x20"); sys.path.insert(0, str(WT / "scripts_project"))
D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
import os   # noqa: E402
MAIN, OFF, TAG = os.environ.get("X20_MAIN", "v5main"), os.environ.get("X20_OFF", "v5off"), os.environ.get("X20_TAG", "")   # C segment: c2main / c2off / _C2
import v4_common as C4   # noqa: E402
import v5_common as V5   # noqa: E402
from scenario_network import config_sha   # noqa: E402

out, delta = {}, []
for lab, sub in (("F1", "integrated/integrated_2920_3h"), ("F2", "no_new_xb/no_new_xb_2920_3h")):
    n5 = pypsa.Network(str(D / f"builds/{MAIN}/{sub}_unsolved.nc")); n0 = pypsa.Network(str(D / f"builds/{OFF}/{sub}_unsolved.nc"))
    m = n5.meta; R = m["research_config"]; cfg = {"research": R}
    rec = m.get("v5_x20") or {}
    r = dict(switch_sha256=rec.get("switch_sha256"), switch_sha_is_main=rec.get("switch_sha256") == V5.switch_sha(V5.V5_MAIN), main_set=rec.get("main_set"),
             v4_tables_dir=(m.get("v4_w08") or {}).get("tables_dir"), b12_identity=m.get("research_config_sha256") == config_sha(R))
    try:
        r["check_network_meta_v4"] = C4.check_network_meta(m, cfg, WT); r["check_network_meta_v5"] = V5.check_network_meta_v5(m, cfg)
    except Exception as e:   # noqa: BLE001
        r["check_error"] = f"{type(e).__name__}: {e}"[:400]
    L = rec.get("ledgers", {})
    g5, g0 = n5.generators, n0.generators
    cty5 = g5.bus.map(n5.buses.country)
    r["S3"] = dict(
        tables={k: v.get("sha256") for k, v in (rec.get("tables") or {}).items()},
        s2_geothermal_in_service_mw=(L.get("lifetime_2_5") or {}).get("s2_geothermal_in_service_mw"),
        gem_additions=(L.get("lifetime_2_5") or {}).get("gem_additions_table"),
        gem_coord_moves=[x for x in ((L.get("gem_coord_2_6") or {}).get("moved") or [])],
        ph_dc=dict(before=(L.get("ph_dc_2_1") or {}).get("total_before_mw"), after=(L.get("ph_dc_2_1") or {}).get("total_after_mw")),
        ac_dedup=dict(lines=(L.get("ac_dedup_2_2") or {}).get("lines"), before=(L.get("ac_dedup_2_2") or {}).get("s_nom_before_mw"), after=(L.get("ac_dedup_2_2") or {}).get("s_nom_after_mw")),
        geothermal_caps=dict(ID=((L.get("geothermal_1_6") or {}).get("ID")), PH_rebuild={k: v for k, v in ((L.get("geothermal_1_6") or {}).get("PH_rebuild") or {}).items() if k != "nodes"}),
        geothermal_existing_mw_by_country={c: float(g5.loc[(g5.carrier == "geothermal existing") & (cty5 == c), "p_nom"].sum()) for c in ("ID", "PH")},
        geothermal_new_cap_mw_by_country={c: float(g5.loc[(g5.carrier == "geothermal") & (cty5 == c) & g5.p_nom_extendable, "p_nom_max"].sum()) for c in ("ID", "PH", "MY", "VN")},
        distribution=dict({k: v for k, v in (L.get("distribution_grid_3_4") or {}).items() if k not in ("loads_by_carrier", "links_by_carrier")},
                          loads_by_carrier=(L.get("distribution_grid_3_4") or {}).get("loads_by_carrier"), links_by_carrier=(L.get("distribution_grid_3_4") or {}).get("links_by_carrier")),
        onwind=L.get("onwind_1_1"), offwind_premium=L.get("offwind_premium_1_3"),
        existing_profiles=pd.DataFrame((L.get("existing_profiles_1_2_q12") or [])).groupby("basis").mw.sum().round(1).to_dict() if L.get("existing_profiles_1_2_q12") else None,
        hooks=sorted(m.get("required_constraint_hooks", [])))
    caps = m.get("external_annual_caps", {}); gp = g5[g5.carrier == "gas production"]
    r["S3"]["gas_cap_twh_by_country"] = {str(c): round(sum(float(caps.get(x, 0)) for x in d.index) / 1e6, 4) for c, d in gp.groupby(gp.bus.map(n5.buses.country))}
    gp0 = g0[g0.carrier == "gas production"]; caps0 = n0.meta.get("external_annual_caps", {})
    r["S3"]["gas_cap_twh_by_country_v5off"] = {str(c): round(sum(float(caps0.get(x, 0)) for x in d.index) / 1e6, 4) for c, d in gp0.groupby(gp0.bus.map(n0.buses.country))}
    h5, h0 = n5.meta.get("research_hydro_inflow", {}), n0.meta.get("research_hydro_inflow", {})
    r["S3"]["hydro_existing_inflow_twh"] = dict(v5=round(sum(v["energy_after_mwh"] for v in (h5.get("countries") or {}).values()) / 1e6, 3), v5off=round(sum(v["energy_after_mwh"] for v in (h0.get("countries") or {}).values()) / 1e6, 3),
                                                v5_by_country={c: round(v["energy_after_mwh"] / 1e6, 3) for c, v in (h5.get("countries") or {}).items()},
                                                v5off_by_country={c: round(v["energy_after_mwh"] / 1e6, 3) for c, v in (h0.get("countries") or {}).items()})
    w = n5.snapshot_weightings.generators
    for nm, nn in (("v5", n5), ("v5off", n0)):
        g = nn.generators; on = g.index[(g.carrier == "onwind") & g.p_nom_extendable]
        P = nn.generators_t.p_max_pu
        cf = (P[[x for x in on if x in P]].mul(w, axis=0).sum() / w.sum())
        r["S3"].setdefault("onwind_candidate_cf_pnom_max_weighted", {})[nm] = float((cf * g.loc[cf.index, "p_nom_max"]).sum() / g.loc[cf.index, "p_nom_max"].sum())
    out[lab] = r
    for comp in ("Bus", "Generator", "Link", "Load", "Line", "StorageUnit", "Store"):
        a, b = n0.df(comp), n5.df(comp)
        for car in sorted(set(a.carrier.astype(str)) | set(b.carrier.astype(str))):
            na, nb = int((a.carrier.astype(str) == car).sum()), int((b.carrier.astype(str) == car).sum())
            col = {"Generator": "p_nom", "Link": "p_nom", "StorageUnit": "p_nom", "Store": "e_nom", "Line": "s_nom"}.get(comp)
            ca = float(a.loc[a.carrier.astype(str) == car, col].sum()) if col else np.nan; cb = float(b.loc[b.carrier.astype(str) == car, col].sum()) if col else np.nan
            if na != nb or (col and abs(ca - cb) > 1e-6):
                delta.append(dict(network=lab, component=comp, carrier=car, count_v5off=na, count_v5=nb, cap_v5off=ca, cap_v5=cb, cap_delta=cb - ca))
    del n5, n0
import yaml   # noqa: E402
b = yaml.safe_load((WT / "configs/research/baseline.yaml").read_text())["research"]["demand"]["v5"]
out["S2_defaults"] = dict(baseline_v5_enabled=b["enabled"], listed_equal_main=all(b[k] == V5.V5_MAIN[k] for k in V5.V5_MAIN if k != "enabled"),
                          v5off_vs_w14={p.name: json.loads(p.read_text())["data_identical"] for p in sorted((D / "evidence").glob(f"V5OFF{TAG}_VS_W14_*.json"))})
pd.DataFrame(delta).to_csv(D / f"evidence/V5_COMPONENT_DELTA{TAG}.csv", index=False, lineterminator="\n")
(D / f"evidence/V5_STATIC_CHECKS{TAG}.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "S3"} if isinstance(v, dict) else v) for k, v in out.items()}, indent=1, default=str)[:3000])
print(pd.DataFrame(delta).to_string()[:6000])
