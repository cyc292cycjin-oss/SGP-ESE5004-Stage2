"""只读诊断：v5main 与 v5off 的 F1 2920 网络在 DC / B2B 链路、陆上风电候选、气原料负荷、专用电源链路上的逐组件差异。用法：python 67b_diag.py"""
import sys
from pathlib import Path

import pandas as pd
import pypsa

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
n5 = pypsa.Network(str(D / "builds/v5main/integrated/integrated_2920_3h_unsolved.nc")); n0 = pypsa.Network(str(D / "builds/v5off/integrated/integrated_2920_3h_unsolved.nc"))
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
for car in ("DC", "B2B", "dedicated plant source"):
    a = n0.links[n0.links.carrier == car][["bus0", "bus1", "p_nom", "p_nom_extendable", "p_nom_max"]]; b = n5.links[n5.links.carrier == car][["p_nom", "p_nom_extendable", "p_nom_max"]]
    j = a.join(b, rsuffix="_v5", how="outer"); j = j[(j.p_nom != j.p_nom_v5) | (j.p_nom_max != j.p_nom_max_v5)]
    print("==", car); print(j.to_string())
a = n0.generators.index[n0.generators.carrier == "onwind"]; b = n5.generators.index[n5.generators.carrier == "onwind"]
print("== onwind only v5off", sorted(set(a) - set(b)), "only v5", sorted(set(b) - set(a)))
print(n0.generators.loc[sorted(set(a) - set(b)), ["bus", "p_nom_max", "p_nom_extendable"]].to_string())
w = n0.snapshot_weightings.generators
for nm, nn in (("v5off", n0), ("v5", n5)):
    L = nn.loads[nn.loads.carrier == "gas feedstock"]
    e = sum(float((nn.loads_t.p_set[x] * w).sum()) if x in nn.loads_t.p_set else float(nn.loads.at[x, "p_set"] * w.sum()) for x in L.index)
    print("== gas feedstock", nm, len(L), "TWh", round(e / 1e6, 3), "by country", (L.bus.map(nn.buses.country).value_counts().to_dict()))
    print({x: round((float((nn.loads_t.p_set[x] * w).sum()) if x in nn.loads_t.p_set else float(nn.loads.at[x, "p_set"] * w.sum())) / 1e6, 3) for x in L.index})
