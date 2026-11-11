"""只读：比较 v5main 与 v5off F1 2920 网络 meta 中 research_dedicated_lines 的差异，并列出 v5 剖面类别表中 SG 的行。用法：python 67c_meta_cmp.py"""
import json
from pathlib import Path

import netCDF4
import pandas as pd

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111"); WT = Path("/home/jin/wt_v5_x20")
def meta(p):
    ds = netCDF4.Dataset(str(p)); m = json.loads(ds.getncattr("meta")); ds.close(); return m
a = meta(D / "builds/v5off/integrated/integrated_2920_3h_unsolved.nc"); b = meta(D / "builds/v5main/integrated/integrated_2920_3h_unsolved.nc")
x, y = a.get("research_dedicated_lines"), b.get("research_dedicated_lines")
print("dedicated keys", sorted(x) if isinstance(x, dict) else type(x))
for k in sorted(set(x) | set(y)):
    sx, sy = json.dumps(x.get(k), sort_keys=True, default=str), json.dumps(y.get(k), sort_keys=True, default=str)
    if sx != sy:
        print("DIFF", k, "\n  v5off", sx[:1500], "\n  v5   ", sy[:1500])
for f in ("S4A_PROFILE_CLASSES_calibrated_gwa_v5_c3.csv", "S4A_PROFILE_CLASSES_calibrated_gwa_v5_c1.csv"):
    t = pd.read_csv(WT / "research_inputs/renewable_v5" / f)
    print(f, t.columns.tolist()[:12], "rows", len(t))
    col = [c for c in t.columns if c in ("node", "bus", "country")]
    print(t[t[col[0]].astype(str).str.startswith("SG")].to_string()[:800] if col else "no node col")
