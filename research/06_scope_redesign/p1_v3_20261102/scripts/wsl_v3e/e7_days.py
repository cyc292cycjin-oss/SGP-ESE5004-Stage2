"""V3 supplement 06, read-only side check: daily means of one EV load by explicit reshape (365 x 8), with day names, first three weeks."""
import numpy as np
import pandas as pd
import xarray as xr
ds = xr.open_dataset("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_op/integrated/integrated_2920_3h_unsolved.nc")
names = ds["loads_t_p_set_i"].values.astype(str); j = list(names).index("TH2 3 land transport EV")
v = ds["loads_t_p_set"].values[:, j]; d = v.reshape(365, 8).mean(axis=1); d = d / d.mean()
days = pd.date_range("2013-01-01", periods=365, freq="D")
print([f"{x.strftime('%a %m-%d')} {y:.3f}" for x, y in zip(days[:21], d[:21])])
print("by name", pd.Series(d, index=days.day_name()).groupby(level=0).mean().round(4).to_dict())
sn = pd.DatetimeIndex(pd.to_datetime(ds["snapshots_snapshot"].values)); print("sn[::8][:3]", sn[::8][:3].tolist(), "sn.dayofweek[:24:8]", list(sn.dayofweek[:24:8]))
s = pd.Series(v, index=sn); print("groupby dayofweek", (s / s.mean()).groupby(sn.dayofweek).mean().round(4).to_dict())
print("groupby day_name", (s / s.mean()).groupby(sn.day_name()).mean().round(4).to_dict())
