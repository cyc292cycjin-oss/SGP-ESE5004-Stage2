"""v3 smoke against the v2 smoke (same 56 snapshots): cost by carrier, capacities, cross-border build. Read-only."""
import json, logging, sys
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
from pathlib import Path
import pandas as pd
logging.disable(logging.WARNING)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
V3 = M / "v3/smoke_r2"; V2 = M / "dfx_v3/smoke_v2"
c = pd.read_csv(V3 / "integrated/COMPONENT_COST_BREAKDOWN.csv", nrows=3); print(list(c.columns)); print(c.head(2).to_string()[:500])
print(json.dumps(json.loads((V3 / "integrated/COMPONENT_COST_BREAKDOWN_SUMMARY.json").read_text()), default=str)[:700])
for lab, d, sc in (("v3_int", V3, "integrated"), ("v3_nnx", V3, "no_new_xb"), ("v2_int", V2, "integrated"), ("v2_dis", V2, "disconnected")):
    g = json.loads((d / sc / "V5_GATES.json").read_text())["A3"]["details"]["objective_reconciliation"]
    print(lab, {k: round(v / 1e9, 3) for k, v in g.items()})
l = {k: pd.read_csv(d / sc / "COUNTRY_COST_LEDGER.csv", index_col=0) for k, d, sc in (("v3_int", V3, "integrated"), ("v3_nnx", V3, "no_new_xb"), ("v2_int", V2, "integrated"), ("v2_dis", V2, "disconnected"))}
print(list(l["v3_int"].columns)[:12])
t = pd.DataFrame({k: v["total"] / 1e9 for k, v in l.items()}); t["b6_v3"] = t.v3_nnx - t.v3_int; t["b6_v2"] = t.v2_dis - t.v2_int; t["int_v3_v2"] = t.v3_int - t.v2_int
print(t.round(3).to_string())
print(t.sum().round(3).to_dict())
