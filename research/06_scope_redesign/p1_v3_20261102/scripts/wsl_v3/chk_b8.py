import logging, sys
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
import pypsa
from v5.v5_gates import gate_b8_demand_consistency
logging.disable(logging.WARNING)
B = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds"
import importlib
s = importlib.import_module("s2_solve")
for sc in ("integrated", "no_new_xb"):
    for tr in (8, 56, 0):
        n = pypsa.Network(f"{B}/{sc}/{sc}_2920_3h_unsolved.nc")
        if tr:
            n.set_snapshots(n.snapshots[:tr]); s.set_representative_weights(n)
        g = gate_b8_demand_consistency(n)
        print(sc, tr, "passed", g["passed"], "worst", max(((abs(v["rel"] or 0), k) for k, v in g["sector_totals"].items())), "Transport rel", g["sector_totals"]["Transport"]["rel"], "first", n.snapshots[0], "last", n.snapshots[-1])
n = pypsa.Network(f"{B}/integrated/integrated_365_24h_unsolved.nc")
g = gate_b8_demand_consistency(n); print("365", g["passed"], max(((abs(v["rel"] or 0), k) for k, v in g["sector_totals"].items())))
