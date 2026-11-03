import json, re, sys, netCDF4
ds = netCDF4.Dataset(sys.argv[1]); meta = json.loads(ds.getncattr("meta")); ds.close()
hits = []
def walk(d, p=()):
    if isinstance(d, dict):
        for k, v in d.items(): walk(v, p + (str(k),))
    elif isinstance(d, list):
        for i, v in enumerate(d): walk(v, p + (str(i),))
    elif isinstance(d, str) and (d.endswith(".py") or ".py:" in d or "scripts_project" in d or "registry_v5/DATA_REGISTRY" in d or "baseline.yaml" in d):
        hits.append((".".join(p), d[:160]))
walk(meta)
for h in hits[:40]: print(h)
print(len(hits))
