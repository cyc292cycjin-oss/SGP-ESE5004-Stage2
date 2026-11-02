import importlib, logging, sys
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
import pypsa
from v5.v5_gates import gate_b8_demand_consistency
logging.disable(logging.WARNING)
B = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds"
s = importlib.import_module("s2_solve")
for tr in (8, 56):
    n = pypsa.Network(f"{B}/integrated/integrated_2920_3h_unsolved.nc")
    n.set_snapshots(n.snapshots[:tr]); s.set_representative_weights(n)
    g = gate_b8_demand_consistency(n)
    rows = sorted(((abs(v["rel"] or 0.0), k, v["rel"], v["expected_mwh"]) for k, v in g["sector_totals"].items()), reverse=True)
    print(tr, "checks", g["checks"])
    print(tr, "top", [(k, r, round(e / 1e6, 2)) for _, k, r, e in rows[:4]])
    p = n.get_switchable_as_dense("Load", "p_set").sum().sum() if tr == 0 else None
    l = n.loads[n.loads.sector.astype(str) == "Transport"]
    print(tr, "Transport carriers", l.carrier.astype(str).value_counts().to_dict(), "varying", sorted(set(l.carrier[[c for c in l.index if c in n.loads_t.p_set.columns]].astype(str))))
r8 = None
