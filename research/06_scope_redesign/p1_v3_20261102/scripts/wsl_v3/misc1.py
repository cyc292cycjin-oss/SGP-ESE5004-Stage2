"""V3 phase 1: ports, routes, current node shares of industry, demand table format, solved V1 liquids. Read only."""
import json, tarfile, sys
from pathlib import Path
import numpy as np, pandas as pd
pd.set_option("display.width", 230); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 120); pd.set_option("display.max_colwidth", 60)
W = Path("/home/jin/wt_v3_20261102"); MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); OUT = MAIN / "results_project/v3/phase1"
p = pd.read_csv(W / "research_inputs/co2_v5/PORTS_ASEAN_TO_NODES_S4D1.csv"); print("PORTS", p.shape, p.columns.tolist()); print(p.groupby("country").size().to_dict() if "country" in p else ""); print(p.head(3).to_string())
r = pd.read_csv(W / "research_inputs/co2_v5/CO2_SHIP_ROUTES_S4D2.csv"); print("ROUTES", r.shape, r.columns.tolist()); print(r.head(3).to_string())
print("origins", r.origin.nunique(), "receivers", sorted(r.receiver.unique()), "sea_km", r.sea_km.describe().round(0).to_dict(), "ratio sea/gc", (r.sea_km / r.gc_km).describe().round(3).to_dict())
c = pd.read_csv(W / "research_inputs/co2_v5/COASTAL_NODES_S4D1_FINAL.csv"); print("COAST", c.columns.tolist(), c.groupby("country").coastal.agg(["sum", "size"]).T.to_dict() if "country" in c else c.coastal.sum())
l = pd.read_csv(W / "research_inputs/co2_v5/LAO_TRANSIT_S4D1.csv"); print("LAO", l.columns.tolist()); print(l[[x for x in l.columns if x in ("node", "coastal_node_at_point", "route_km", "alt_sea_port", "alt_port_route_km")]].to_string())
d = pd.read_csv("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv", nrows=4); print("DEMAND_v2 cols", d.columns.tolist()); print(d.head(2).to_string()[:700])
d = pd.read_csv("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv")
sc = [x for x in d.columns if x.lower() in ("sector",)]; val = [x for x in d.columns if "twh" in x.lower() or "mwh" in x.lower()]
print(val, d[sc[0]].unique()[:14] if sc else "")
am = json.load(open(MAIN / "results_project/assembly_v1/final_allocation/allocation_manifest.json")); print("alloc keys", list(am.keys())[:10], len(am["records"]))
acc = sorted({x["InputID"].split(":")[3] for x in am["records"]}); print(acc); print(am["records"][0]["InputID"], {k: (v if not isinstance(v, list) else len(v)) for k, v in am["records"][0].items()})
for k in ("method", "rule", "allocation_rule", "notes"):
    if k in am: print(k, str(am[k])[:300])
reg = json.load(open(MAIN / "research_inputs/assembly_v1/registry.json")); rr = reg["records"]; print(rr[0].keys()); ii = [x for x in rr if x.get("Account") in ("IndustryFinalEnergy",)][:1]; print(json.dumps(ii, ensure_ascii=False)[:800])
