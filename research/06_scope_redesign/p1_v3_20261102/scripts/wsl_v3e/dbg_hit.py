"""V3 supplement 06, read-only: compare the stored 3 h e_min_pu of a few EV stores with the hit rule of v3_layers.apply_ev_structure (lines 336-338)."""
import numpy as np
import pandas as pd
import xarray as xr
P = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_op/integrated/integrated_2920_3h_unsolved.nc"
ds = xr.open_dataset(P)
sn = pd.DatetimeIndex(pd.to_datetime(ds["snapshots"].values))
cols = ds["stores_t_e_min_pu_i"].values.astype(str)
tz = pd.read_csv("/home/jin/wt_v3_20261102/research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node").utc_offset_h
print("snapshot dtype", ds["snapshots"].dtype, sn[:3].tolist(), "tz-aware", sn.tz)
for node in ("SG2 0", "TL11 0", "MM2 1", "TH2 3"):
    s = f"{node} EV battery store"; j = list(cols).index(s); v = ds["stores_t_e_min_pu"].values[:, j]
    off = float(tz[node]); lh = (sn.hour.to_numpy() + off) % 24.0
    hit = (lh <= 7.0) & (7.0 < lh + 3.0); hit |= ((lh - 24.0) <= 7.0) & (7.0 < lh - 21.0)
    print(node, "off", off, "stored first 16", v[:16].round(2).tolist())
    print("   rule  first 16", np.where(hit, 0.8, 0.0)[:16].tolist(), "stored==rule", bool(np.array_equal(np.where(hit, 0.8, 0.0), v)), "lh first 8", lh[:8].tolist())
