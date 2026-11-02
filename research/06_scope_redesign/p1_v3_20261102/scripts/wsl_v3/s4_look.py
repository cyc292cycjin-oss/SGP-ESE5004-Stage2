"""Supplement 04: what is attached to the Lao plant-line nodes (reads the one-way 2920x3h network, no solve)."""
import json
import logging
import sys

import pandas as pd
import pypsa

logging.disable(logging.WARNING)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 70)
M = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_oneway/"
n = pypsa.Network(M + "integrated/integrated_2920_3h_unsolved.nc")
print("bus cols", list(n.buses.columns))
print(n.buses.loc[["LA2 1", "LA2 2", "LA2 3", "LA2 4", "LA2 5", "LA2 0"] if "LA2 0" in n.buses.index else ["LA2 1", "LA2 2", "LA2 3", "LA2 4", "LA2 5"]].T)
print("all LA AC", list(n.buses.index[(n.buses.country == "LA") & (n.buses.carrier == "AC")]))
print("gen cols", list(n.generators.columns))
print("su cols", list(n.storage_units.columns))
print("link cols", list(n.links.columns))
print("store cols", list(n.stores.columns))
nodes = [f"LA2 {i}" for i in range(1, 6)]
for b in nodes:
    print("=" * 30, b)
    g = n.generators[n.generators.bus == b]
    print(g[["carrier", "p_nom", "p_nom_extendable", "p_nom_max", "marginal_cost", "capital_cost"]])
    s = n.storage_units[n.storage_units.bus == b]
    print(s[["carrier", "p_nom", "p_nom_extendable", "p_nom_max", "max_hours", "efficiency_dispatch", "efficiency_store"]])
    for p in ("bus0", "bus1", "bus2", "bus3", "bus4"):
        if p not in n.links:
            continue
        l = n.links[n.links[p] == b]
        if len(l):
            print("links at", p, len(l))
            print(l[["carrier", "bus0", "bus1", "p_nom", "p_nom_extendable", "efficiency"]].sort_values(["carrier"]).assign(p_out=lambda d: d.p_nom * d.efficiency))
    print("stores", n.stores[n.stores.bus == b][["carrier", "e_nom", "e_nom_extendable"]])
    print("loads", n.loads[n.loads.bus == b][["carrier", "p_set"]])
    print("lines", n.lines[(n.lines.bus0 == b) | (n.lines.bus1 == b)][["bus0", "bus1", "s_nom", "s_nom_extendable", "border_class"]])
u = pd.DataFrame(n.meta["existing_unit_components"]).T
print(u.columns.tolist())
print(u[u.node.isin(nodes)].sort_values(["node", "component"]).to_string())
print(json.dumps({k: str(v)[:300] for k, v in n.meta.items() if "exist" in k}, indent=0)[:3000])
