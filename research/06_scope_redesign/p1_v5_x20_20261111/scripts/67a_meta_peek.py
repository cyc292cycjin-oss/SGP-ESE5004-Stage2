"""只读：打印 v5main 网络 meta 的顶层键及若干键的结构，不加载网络。用法：python 67a_meta_peek.py <nc>"""
import json
import sys

import netCDF4

ds = netCDF4.Dataset(sys.argv[1]); m = json.loads(ds.getncattr("meta")); ds.close()
print("meta keys", sorted(m))
for k in sorted(m):
    if any(s in k for s in ("cap", "hydro", "inflow", "gas", "hook")):
        v = m[k]; print("KEY", k, type(v).__name__, json.dumps(v, default=str)[:300])
