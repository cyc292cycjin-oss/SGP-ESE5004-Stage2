"""V3 supplement 06, read-only: which screening runs carry EV battery stores and with which e_min_pu; which Stores have time-varying bounds at all."""
import json
from pathlib import Path

import numpy as np
import xarray as xr

X = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T063207Z/full_unpacked/export")
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_op")
OUT = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/evdiag/SCREEN_RUNS_EV.json")
res = {}
for k, p in [("V1", X / "V1/integrated_DFX_365X24H_solved.nc"), ("V2", X / "V2/no_new_xb_DFX_365X24H_solved.nc"), ("V3", X / "V3/disconnected_DFX_365X24H_solved.nc"),
             ("V4", X / "V4/integrated_DFX_365X24H_solved.nc"), ("V5", X / "V5/integrated_DFX_365X24H_solved.nc"),
             ("build 2920x3h integrated", R / "integrated/integrated_2920_3h_unsolved.nc"), ("build 2920x3h no_new_xb", R / "no_new_xb/no_new_xb_2920_3h_unsolved.nc")]:
    ds = xr.open_dataset(p)
    st = [s for s in ds["stores_i"].values.astype(str) if s.endswith(" EV battery store")]
    tv = {v: (sorted({c.rsplit(" ", 2)[-2] + " " + c.rsplit(" ", 1)[-1] if c.endswith(" EV battery store") else c for c in ds[v + "_i"].values.astype(str)})[:5], int(ds[v].shape[1]))
          for v in ("stores_t_e_min_pu", "stores_t_e_max_pu") if v in ds}
    ev_cols = [c for c in ds["stores_t_e_min_pu_i"].values.astype(str)] if "stores_t_e_min_pu" in ds else []
    vals = sorted({round(float(x), 10) for x in np.unique(ds["stores_t_e_min_pu"].values)}) if ev_cols else []
    res[k] = dict(ev_stores=len(st), e_nom_twh=float(ds["stores_e_nom"].to_series().reindex(st).sum() / 1e6) if st else 0.0, time_varying_store_bounds=tv,
                  time_varying_e_min_columns_all_ev=all(c.endswith(" EV battery store") for c in ev_cols), e_min_pu_values=vals)
    ds.close()
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
print(json.dumps(res, ensure_ascii=False, indent=0))
