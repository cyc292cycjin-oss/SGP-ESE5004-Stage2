import json
from pathlib import Path
D = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence"); r = json.loads((D / "V3_STATIC_CHECK.json").read_text())
print("all", r["all_structural_passed"], r["stock_x1"], r["dedicated_lines"], "b5", r["gate_b5_no_new_xb"]["passed"], r["gate_b5_no_new_xb_365"]["passed"], "struct", r["structure_vs_v2"]["passed"])
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_oneway")
print(sorted(set(json.loads((M / "integrated/integrated_BUILD_RECEIPT.json").read_text())["code_sha"][:8] for _ in [0])))
t = [l for l in (M / "bridge.log").read_text().splitlines() if "load TWh" in l or " vs " in l]; print("\n".join(x[:130] for x in t))
