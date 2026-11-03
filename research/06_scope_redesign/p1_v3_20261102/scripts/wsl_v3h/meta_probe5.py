import json, sys, netCDF4
ds = netCDF4.Dataset(sys.argv[1]); meta = json.loads(ds.getncattr("meta")); ds.close()
for pat in ("methanol ship", "oil non-fossil ship", "ammonia ship", "ship_cost", "td_tanker", "ieaghg", "fleet_scale", "ev_fleet_scale", "battery_mwh_total", "BEV charger", "EV battery store"):
    keys = sorted({k for k, v in meta.items() if pat in json.dumps(v)})
    print(f"{pat!r}: {keys}")
print("v3_layers:", json.dumps(meta.get("v3_layers"))[:400])
print("config sha keys:", {k: meta[k] for k in meta if "sha256" in k and isinstance(meta[k], str)})
