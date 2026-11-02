"""Supplement 04: the 350 MW stock wind unit over the full year against the new wind of its node; B1 excess of the integrated smoke. Read-only."""
import json, logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
n = pypsa.Network(str(M / "builds_bound/integrated/integrated_2920_3h_unsolved.nc")); k = "existing_survivor::LA2 1::onwind existing::S4B1"
g = n.generators; pm = n.get_switchable_as_dense("Generator", "p_max_pu")
print(g.loc[k, ["bus", "carrier", "p_nom", "marginal_cost"]].to_dict(), "annual mean p_max_pu", round(float(pm[k].mean()), 4), "max", round(float(pm[k].max()), 4), "by month", pm[k].groupby(pm.index.month).mean().round(3).to_dict())
for c in ("LA2 1 onwind-2025", "LA2 1 onwind-2025 c1", "LA2 1 onwind-2025 c2"):
    print(c, "annual mean", round(float(pm[c].mean()), 4), "max", round(float(pm[c].max()), 3))
e = g[(g.carrier == "onwind existing")]; print("all existing wind", len(e), e.p_nom.sum(), {x: round(float(pm[x].mean()), 3) for x in e.index[:12]})
u = pd.DataFrame(n.meta["existing_unit_components"]).T; print(u[u.component == k][["capacity_mw", "node", "source", "commissioning_year", "gem_status"]].to_string())
b = json.loads((M / "smoke_s4/integrated/V5_GATES.json").read_text())["B1"]
c = b["countries"]; rows = {x: {a: (round(v, 4) if isinstance(v, float) else v) for a, v in z.items()} for x, z in c.items()} if isinstance(c, dict) else c
print(json.dumps(rows, default=str)[:1500])
