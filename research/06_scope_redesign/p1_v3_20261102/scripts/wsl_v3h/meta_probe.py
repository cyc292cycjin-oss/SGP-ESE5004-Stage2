import json, sys, netCDF4
p = sys.argv[1]
ds = netCDF4.Dataset(p)
attrs = {k: ds.getncattr(k) for k in ds.ncattrs()}
print("global attrs:", list(attrs))
meta = json.loads(attrs.get("meta", "{}")) if isinstance(attrs.get("meta"), str) else {}
print("meta keys:", sorted(meta))
s = json.dumps(meta)
for pat in ("/home/jin", "wt_v3", "results_project", "/mnt/"):
    i = s.find(pat); print(pat, s.count(pat), s[max(0,i-200):i+120] if i >= 0 else "")
ds.close()
