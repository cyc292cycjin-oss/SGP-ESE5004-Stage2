import json, sys, netCDF4
def meta(p):
    ds = netCDF4.Dataset(p); m = json.loads(ds.getncattr("meta")); ds.close(); return m
a = meta(sys.argv[1]); b = meta(sys.argv[2])
print("keys only in flat:", sorted(set(b) - set(a)), "only in base:", sorted(set(a) - set(b)))
for k in sorted(b):
    if "overrid" in json.dumps(b[k])[:100000] and k not in ("s2_layers",):
        s = json.dumps(b[k]); i = s.find("overrid"); print(k, s[max(0, i-200):i+200])
v = meta(sys.argv[3]).get("research_variant"); print("variant:", json.dumps(v)[:600])
