"""V3 supplement 06, read-only side check: the 168-hour local EV week, hour by hour for Thu-Mon, and UTC-day means implied for a +7 h node."""
import numpy as np
import pandas as pd
w = pd.read_csv("/home/jin/wt_v3_20261102/research_inputs/transport_v3/EV_WEEKLY_LOCAL_SHAPE_V3.csv").sort_values(["weekday", "hour"])
c = w.consumption_norm.to_numpy()
for d, nm in [(3, "Thu"), (4, "Fri"), (5, "Sat"), (6, "Sun"), (0, "Mon")]:
    print(nm, " ".join(f"{x:.2f}" for x in c[24 * d: 24 * d + 24]), "mean", round(float(c[24 * d: 24 * d + 24].mean()), 4))
for off in (7.0, 8.0):
    print("UTC-day means for offset", off, [round(float(np.mean([c[int(24 * d + off + k) % 168] for k in range(24)])), 4) for d in range(7)])
