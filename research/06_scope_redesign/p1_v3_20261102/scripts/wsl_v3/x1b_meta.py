"""X1b: existing LA units named in the network meta (existing_unit_components). Read-only."""
import json
from pathlib import Path
import netCDF4 as nc
import pandas as pd
f = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds/integrated/integrated_365_24h_unsolved.nc")
with nc.Dataset(f) as d:
    m = json.loads(d.getncattr("meta"))
u = m["existing_unit_components"]; print(len(u)); k = next(iter(u)); print(k, json.dumps(u[k], default=str)[:700])
la = {k: v for k, v in u.items() if "LA2" in k or str(v.get("country", v.get("Country", ""))) == "LA" or str(v.get("bus", v.get("node", ""))).startswith("LA")}
print("LA entries", len(la))
for k, v in sorted(la.items(), key=lambda t: -float(t[1].get("capacity_mw", 0) or 0)):
    print(k, json.dumps({a: b for a, b in v.items() if a not in ("resource_identity",)}, default=str)[:520])
print({k: (len(v) if hasattr(v, "__len__") else v) for k, v in m.items() if "exist" in k or "stock" in k or "fleet" in k or "asset" in k})
