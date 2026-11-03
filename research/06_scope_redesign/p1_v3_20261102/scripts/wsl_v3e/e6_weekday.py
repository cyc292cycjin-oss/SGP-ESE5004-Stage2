"""V3 supplement 06, read-only side check: weekday alignment of the stored land transport EV load against v3_ev.ev_series (D165-3 a: 2013 calendar,
local weekday). Recomputes the series from the shape file and the stored snapshots; compares; reports weekday means by UTC and by local day."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
from v3_ev import ev_series  # noqa: E402

W = Path("/home/jin/wt_v3_20261102"); R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
OUT = W / "research/06_scope_redesign/p1_v3_20261102/evidence/evdiag/EV_WEEKDAY_CHECK.json"
shape = pd.read_csv(W / "research_inputs/transport_v3/EV_WEEKLY_LOCAL_SHAPE_V3.csv").sort_values(["weekday", "hour"])
tz = pd.read_csv(W / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node").utc_offset_h
ds = xr.open_dataset(R / "builds_op/integrated/integrated_2920_3h_unsolved.nc")
sn = pd.DatetimeIndex(pd.to_datetime(ds["snapshots_snapshot"].values)); raw = ds["snapshots"].values
L = pd.DataFrame(ds["loads_t_p_set"].values, index=sn, columns=ds["loads_t_p_set_i"].values.astype(str))
res = dict(snapshot_coord_first=[str(x) for x in raw[:3]], snapshot_ts_first=[str(x) for x in sn[:3]], first_day=str(sn[0].day_name()))
rows = {}
for node in ("TH2 3", "SG2 0", "MM2 1", "TL11 0"):
    s = L[f"{node} land transport EV"]; x = ev_series(sn, float(tz[node]), shape.consumption_norm.to_numpy()); x = x / x.mean() * s.mean()
    local = sn + pd.Timedelta(hours=float(tz[node]))
    rows[node] = dict(equal_to_ev_series=bool(np.allclose(s.to_numpy(), x, rtol=1e-12, atol=1e-9)),
                      utc_weekday_mean={str(k): round(float(v), 4) for k, v in (s / s.mean()).groupby(sn.dayofweek).mean().items()},
                      local_weekday_mean={str(k): round(float(v), 4) for k, v in (s / s.mean()).groupby(local.dayofweek).mean().items()},
                      first_8_over_mean=[round(float(v), 3) for v in (s / s.mean()).iloc[:8]])
res["nodes"] = rows
res["shape_weekday_mean_mon0"] = {str(k): round(float(v), 4) for k, v in shape.groupby("weekday").consumption_norm.mean().items()}
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
print(json.dumps(res, ensure_ascii=False, indent=0))
