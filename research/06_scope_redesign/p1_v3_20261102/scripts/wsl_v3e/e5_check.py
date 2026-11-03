"""V3 supplement 06, read-only: (a) the 56-snapshot smoke e_min_pu equals the first 56 rows of the 2920x3h build; (b) the EV load shape left at
365x24h (weekly only); (c) the convexity bracket of the EV effect under the upstream max rule (arithmetic on the recorded numbers)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
X = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T063207Z/full_unpacked/export")
OUT = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/evdiag")


def frame(p, v):
    ds = xr.open_dataset(p); f = pd.DataFrame(ds[v].values, index=pd.to_datetime(ds["snapshots_snapshot"].values), columns=ds[v + "_i"].values.astype(str)); ds.close(); return f


res = {}
full = frame(R / "builds_op/integrated/integrated_2920_3h_unsolved.nc", "stores_t_e_min_pu")
for k in ("smoke_s5/integrated/integrated_SMOKE_TEST_ONLY_solved.nc", "smoke_s5/no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc", "smoke_s1/integrated/integrated_SMOKE_TEST_ONLY_solved.nc"):
    s = frame(R / k, "stores_t_e_min_pu")
    res["smoke_equals_first_56_of_2920:" + k.split("/")[0] + "/" + k.split("/")[1]] = bool(s.shape == (56, 96) and np.array_equal(s.to_numpy(), full.loc[s.index, s.columns].to_numpy()))
L = frame(X / "V1/integrated_DFX_365X24H_solved.nc", "loads_t_p_set"); L = L[[c for c in L.columns if c.endswith(" land transport EV")]].sum(axis=1)
r = L / L.mean(); wd = r.groupby(r.index.dayofweek).mean()
res["v1_daily_ev_load"] = dict(mean_gw=float(L.mean() / 1e3), min_over_mean=float(r.min()), max_over_mean=float(r.max()), by_weekday_mon0={int(k): round(float(v), 4) for k, v in wd.items()},
                               max_abs_deviation_gw=float((L - L.mean()).abs().max() / 1e3))
S = json.loads((OUT / "EV_SOC_SUMMARY.json").read_text())["V1"]; C = json.loads((OUT / "COST_V5_V1_SUMMARY.json").read_text())
B1 = C["objective"]["diff_bn"]; rent = S["storage_rent_bn_eur"]; s = 0.2 / 0.9
res["bracket"] = dict(note="lossless cyclic zero-cost store: band [0.8,1] e_nom is LP-equivalent to scaling the current [0.1,1] band by s = 0.2/0.9; value function convex in s; B(1) taken as V5 - V1",
                      s=s, B1_bn=B1, rent_at_s1_bn=rent, ev_effect_max_rule_lower_bn=s * B1, ev_effect_max_rule_upper_bn=B1 - (1 - s) * rent,
                      relaxation_part_lower_bn=B1 - (B1 - (1 - s) * rent), relaxation_part_upper_bn=B1 - s * B1,
                      relaxation_share=[(1 - s) * rent / B1, (1 - s)])
(OUT / "EV_CHECKS.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
print(json.dumps(res, ensure_ascii=False, indent=0))
