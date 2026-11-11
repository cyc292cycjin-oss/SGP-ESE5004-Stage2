"""X20 §3 第 3 步：v5off（v5 关闭）构建与 W14 构建的回归比较 —— 每个 netCDF 数据变量逐值比较（NaN 视为相等），meta 逐顶层键比较。只读。
用法：python 66_v5off_regression.py <W14 nc> <v5off nc> <输出 json>"""
import json
import sys

import numpy as np
import xarray as xr

a_p, b_p, out = sys.argv[1], sys.argv[2], sys.argv[3]
A = xr.open_dataset(a_p); B = xr.open_dataset(b_p)
va, vb = set(A.data_vars) | set(A.coords), set(B.data_vars) | set(B.coords)
res = dict(w14=a_p, v5off=b_p, only_w14=sorted(va - vb), only_v5off=sorted(vb - va), differing=[], compared=0)
for v in sorted(va & vb):
    x, y = A[v].values, B[v].values
    res["compared"] += 1
    if x.shape != y.shape:
        res["differing"].append(dict(var=v, why=f"shape {x.shape} vs {y.shape}")); continue
    if x.dtype.kind in "fc":
        same = np.array_equal(x, y, equal_nan=True)
    else:
        same = np.array_equal(x.astype(str), y.astype(str))
    if not same:
        res["differing"].append(dict(var=v, why="values"))
ma, mb = json.loads(A.attrs.get("meta", "{}")), json.loads(B.attrs.get("meta", "{}"))
res["meta_keys_only_w14"] = sorted(set(ma) - set(mb)); res["meta_keys_only_v5off"] = sorted(set(mb) - set(ma))
res["meta_keys_differing"] = sorted(k for k in set(ma) & set(mb) if json.dumps(ma[k], sort_keys=True, default=str) != json.dumps(mb[k], sort_keys=True, default=str))
A.close(); B.close()
res["data_identical"] = not res["differing"] and not res["only_w14"] and not res["only_v5off"]
open(out, "w").write(json.dumps(res, indent=1) + "\n")
print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 30 else v[:30] + ["..."]) for k, v in res.items()}, indent=1))
