import logging, sys
import pandas as pd, pypsa
logging.disable(logging.WARNING)
B = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds"
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102"
n = pypsa.Network(f"{B}/integrated/integrated_2920_3h_unsolved.nc")
w = n.snapshot_weightings.generators
p = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum() / 1e6
l = n.loads.assign(twh=p.reindex(n.loads.index).fillna(0.0))
print(l.columns.tolist())
pd.set_option("display.width", 220, "display.max_rows", 200, "display.max_columns", 30)
print(l.groupby(["carrier", "sector"]).twh.agg(["sum", "count"]).round(2))
t = pd.read_csv(f"{D}/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v3.csv")
print(t.columns.tolist()); print(t.head(3).to_string())
print(t.groupby(["carrier", "sector"]).twh.sum().round(2))
L = n.links
new = [x for x in L.index[L.carrier == "oil pool"]]
v2 = pypsa.Network("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc")
add = sorted(set(new) - set(v2.links.index))
print("added oil pool:", add)
for a in add:
    b = L.at[a, "bus0"]
    print(a, b, n.buses.at[b, "country"], L[(L.bus0 == b) | (L.bus1 == b)].carrier.value_counts().to_dict(), "loads", n.loads[n.loads.bus == b].carrier.tolist())
