import json, sys, netCDF4
ds = netCDF4.Dataset(sys.argv[1]); meta = json.loads(ds.getncattr("meta")); ds.close()
s = json.dumps(meta)
for pat in ("ef1d6cdd", "DATA_REGISTRY", "registry_sha", "tier"):
    i = s.find(pat); print(pat, s.count(pat), s[max(0,i-150):i+100] if i >= 0 else "")
print("research_liquids:", json.dumps(meta.get("research_liquids"))[:600])
print("research_ev:", json.dumps(meta.get("research_ev")))
rc = meta.get("research_config", {}); print("liquids cfg:", rc.get("liquids")); print("ev cfg keys:", {k: v for k, v in rc.get("s2", {}).get("demand", {}).items() if "ev" in k})
print("overrides:", meta.get("research_config_overrides"), [k for k in meta if "overrid" in k])
