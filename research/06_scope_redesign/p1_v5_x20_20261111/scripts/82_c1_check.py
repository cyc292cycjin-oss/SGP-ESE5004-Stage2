"""X20 C-1 核对（只读，不求解）：C-1 预构建（builds/c1pre）与 B 段 v5 主集（builds/v5main）的 F1 2920x3h 网络对照。
  (1) 逐个 netCDF 变量比较：除了新建候选的入流（storage_units_t_inflow 中 hydro 候选列）与 ror 候选的 p_max_pu，其余应逐值相同；
  (2) 存量（hydro existing 入流、ror existing p_max_pu）逐值相同 = "存量总入流不变"；
  (3) 各国候选的年 CF：B 段（operating_only）与 C-1（national_capacity）对照，水库 CF 应等于表值，ror 为截断后值；
  (4) meta v5_x20 记录：开关 SHA = 新主集，表 SHA = 表文件。
用法：python 82_c1_check.py   输出 evidence/C1_HYDRO_CANDIDATE_CHECK.json 与 C1_HYDRO_CANDIDATE_CF.csv"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import xarray as xr

WT = Path("/home/jin/wt_v5_x20"); sys.path.insert(0, str(WT / "scripts_project"))
D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
import v5_common as V5   # noqa: E402
import v5_layers as L   # noqa: E402

a_p = D / "builds/v5main/integrated/integrated_2920_3h_unsolved.nc"; b_p = D / "builds/c1pre/integrated/integrated_2920_3h_unsolved.nc"
A, B = xr.open_dataset(a_p), xr.open_dataset(b_p)
res = dict(b_segment=str(a_p), c1=str(b_p), differing=[], compared=0)
for v in sorted(set(A.data_vars) | set(A.coords)):
    if v not in B:
        res["differing"].append(dict(var=v, why="missing in c1")); continue
    x, y = A[v].values, B[v].values; res["compared"] += 1
    same = (x.shape == y.shape) and (np.array_equal(x, y, equal_nan=True) if x.dtype.kind in "fc" else np.array_equal(x.astype(str), y.astype(str)))
    if not same:
        res["differing"].append(dict(var=v, why="values" if x.shape == y.shape else f"shape {x.shape} vs {y.shape}"))
A.close(); B.close()
na, nb = pypsa.Network(str(a_p)), pypsa.Network(str(b_p))
w = na.snapshot_weightings.generators
su, g = na.storage_units, na.generators
cand_su = su.index[(su.carrier == "hydro") & su.p_nom_extendable & (su.p_nom_max > 0)]
cand_g = g.index[(g.carrier == "ror") & g.p_nom_extendable & (g.p_nom_max > 0)]
ex_su = su.index[su.carrier == "hydro existing"]; ex_g = g.index[g.carrier == "ror existing"]
ia, ib = na.storage_units_t.inflow, nb.storage_units_t.inflow; pa, pb = na.generators_t.p_max_pu, nb.generators_t.p_max_pu
res["inflow_columns_differing"] = sorted(c for c in ia.columns if not np.array_equal(ia[c].values, ib[c].values))
res["p_max_pu_columns_differing"] = sorted(c for c in pa.columns if not np.array_equal(pa[c].values, pb[c].values))
res["only_candidates_differ"] = set(res["inflow_columns_differing"]) <= set(cand_su) and set(res["p_max_pu_columns_differing"]) <= set(cand_g)
res["existing_unchanged"] = bool(all(np.array_equal(ia[c].values, ib[c].values) for c in ex_su if c in ia) and all(np.array_equal(pa[c].values, pb[c].values) for c in ex_g if c in pa))
ex_energy = lambda n: float(sum((n.storage_units_t.inflow[c] * w).sum() for c in ex_su if c in n.storage_units_t.inflow) + sum((n.generators_t.p_max_pu[c] * n.generators.at[c, "p_nom"] * w).sum() for c in ex_g if c in n.generators_t.p_max_pu))   # noqa: E731
res["existing_inflow_twh"] = dict(b_segment=ex_energy(na) / 1e6, c1=ex_energy(nb) / 1e6)
tab = pd.read_csv(WT / L.HYDRO_CANDIDATE_TABLE, keep_default_na=False).set_index("country")
rows = []
for kind, idx, getA, getB in (("reservoir", cand_su, lambda c: ia[c] / su.at[c, "p_nom_max"], lambda c: ib[c] / su.at[c, "p_nom_max"]),
                              ("ror", cand_g, lambda c: pa[c], lambda c: pb[c])):
    cty = (su if kind == "reservoir" else g).loc[idx, "bus"].map(na.buses.country)
    for c, names in pd.Series(idx, index=idx).groupby(cty):
        cap = (su if kind == "reservoir" else g).loc[names, "p_nom_max"]
        cfa = float(sum(float((getA(x) * w).sum()) * cap[x] for x in names) / cap.sum() / 8760); cfb = float(sum(float((getB(x) * w).sum()) * cap[x] for x in names) / cap.sum() / 8760)
        rows.append(dict(country=c, kind=kind, candidates=len(names), p_nom_max_mw=float(cap.sum()), cf_b_segment_operating_only=cfa, cf_c1_national_capacity=cfb,
                         cf_table=float(tab.at[c, "cf"]) if c in tab.index and tab.at[c, "status"] == "REGISTERED" else None))
T = pd.DataFrame(rows)
T["c1_minus_table"] = T.cf_c1_national_capacity - T.cf_table
T.to_csv(D / "evidence/C1_HYDRO_CANDIDATE_CF.csv", index=False, lineterminator="\n")
res["reservoir_cf_equals_table_max_abs"] = float(T[T.kind == "reservoir"].c1_minus_table.abs().max())
rec = nb.meta.get("v5_x20") or {}
res["switch_sha256"] = rec.get("switch_sha256"); res["switch_sha_is_new_main"] = rec.get("switch_sha256") == V5.switch_sha(V5.V5_MAIN)
res["table_record"] = (rec.get("tables") or {}).get("hydro_candidate_unit_inflow"); res["table_sha256_now"] = V5.sha256(WT / L.HYDRO_CANDIDATE_TABLE)
res["main_set"] = rec.get("main_set")
(D / "evidence/C1_HYDRO_CANDIDATE_CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
print(json.dumps({k: v for k, v in res.items()}, indent=1, default=str)[:3000])
pd.set_option("display.width", 220); print(T.round(4).to_string())
