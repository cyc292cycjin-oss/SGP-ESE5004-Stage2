"""只读：c2main 与 v5main（B 段）F1 / F2 2920 网络的随时段组件数（内存门槛估计的组件比）。用法：python 69d_counts.py"""
from pathlib import Path

import netCDF4

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
DIMS = ("generators_i", "links_i", "lines_i", "storage_units_i", "stores_i", "loads_i")
for sub in ("integrated/integrated_2920_3h_unsolved.nc", "no_new_xb/no_new_xb_2920_3h_unsolved.nc"):
    c = {}
    for lab in ("v5main", "c2main", "c2off"):
        ds = netCDF4.Dataset(str(D / "builds" / lab / sub)); c[lab] = {d: len(ds.dimensions[d]) for d in DIMS if d in ds.dimensions}; ds.close()
    print(sub, {k: sum(v.values()) for k, v in c.items()}, "c2main == v5main:", c["c2main"] == c["v5main"])
