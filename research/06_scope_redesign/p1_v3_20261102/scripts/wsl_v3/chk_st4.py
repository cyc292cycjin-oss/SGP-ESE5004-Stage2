import json
from pathlib import Path
D = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence"); r = json.loads((D / "V3_STATIC_CHECK.json").read_text())
print("all", r["all_structural_passed"], r["stock_x1"], r["dedicated_lines"], r["plant_sources"], "b5", r["gate_b5_no_new_xb"]["passed"], r["gate_b5_no_new_xb_365"]["passed"], "scen", r["scenario_difference_2920"]["passed"], r["scenario_difference_365"]["passed"], "struct", r["structure_vs_v2"], "demand", r["demand_vs_table"]["passed"])
print({k: (r[k]["orphan_count"], r[k]["weights"]) for k in ("integrated_2920", "no_new_xb_2920", "integrated_365", "no_new_xb_365")})
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_bound")
print(sorted(set(json.loads((M / "integrated/integrated_BUILD_RECEIPT.json").read_text())["code_sha"][:8] for _ in [0])))
t = [l for l in (M / "bridge.log").read_text().splitlines() if "load TWh" in l or " vs " in l]; print("\n".join(x[:140] for x in t))
print((M / "static.log").read_text()[:600])
