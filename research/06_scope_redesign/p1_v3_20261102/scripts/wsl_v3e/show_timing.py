"""V3 supplement 06, read-only: group the 3 h e_min_pu timing table by UTC offset."""
import pandas as pd
t = pd.read_csv("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/evdiag/EMIN_3H_TIMING.csv", dtype=str)
print(t.groupby(["network", "utc_offset_h", "hit_utc_hours", "local_start", "local_end_of_snapshot", "hits"]).size().to_string())
