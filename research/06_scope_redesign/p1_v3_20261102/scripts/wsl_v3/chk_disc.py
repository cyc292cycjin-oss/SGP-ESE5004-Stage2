"""Supplement 03: the disconnected 365x24h network before and after the one-way change: bytes, and where it differs (variables, attributes). Read-only."""
import hashlib, json, sys
import netCDF4 as nc
import numpy as np
a, b = sys.argv[1:3]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
print("DISC_SHA:", sha(a)[:12], sha(b)[:12], "identical" if sha(a) == sha(b) else "differ")
if sha(a) != sha(b):
    x, y = nc.Dataset(a), nc.Dataset(b); diff = []
    vs = set(x.variables) ^ set(y.variables)
    for k in sorted(set(x.variables) & set(y.variables)):
        p, q = x[k][:], y[k][:]
        if np.shape(p) != np.shape(q) or not np.array_equal(np.ma.filled(p, 0) if np.ma.isMaskedArray(p) else p, np.ma.filled(q, 0) if np.ma.isMaskedArray(q) else q):
            diff.append(k)
    at = sorted(k for k in set(x.ncattrs()) | set(y.ncattrs()) if (x.getncattr(k) if k in x.ncattrs() else None) != (y.getncattr(k) if k in y.ncattrs() else None))
    print("DISC_VARIABLES_DIFFER:", len(diff), diff[:8], "only in one:", sorted(vs)[:6], "attrs:", at[:6])
    if "meta" in at:
        m, n = json.loads(x.getncattr("meta")), json.loads(y.getncattr("meta")); print("DISC_META_KEYS:", sorted(k for k in set(m) | set(n) if m.get(k) != n.get(k))[:12])
