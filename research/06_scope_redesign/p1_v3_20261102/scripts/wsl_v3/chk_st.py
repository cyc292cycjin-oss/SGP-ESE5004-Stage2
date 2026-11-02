import json
from pathlib import Path
D = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence")
r = json.loads((D / "V3_STATIC_CHECK.json").read_text())
print("all", r["all_structural_passed"]); print({k: r[k] for k in ("stock_x1", "dedicated_lines")}); print("b5", r["gate_b5_no_new_xb"]["passed"], r["gate_b5_no_new_xb_365"]["passed"], "scen", r["scenario_difference_2920"]["passed"], r["scenario_difference_365"]["passed"], "struct", r["structure_vs_v2"]["passed"], r["structure_vs_v2"]["unexpected"][:6], "demand", r["demand_vs_table"]["passed"], {k: r[k]["orphan_count"] for k in ("integrated_2920", "no_new_xb_2920", "integrated_365", "no_new_xb_365")})
for f in ("X1_STOCK_TABLE_V3.csv", "X1B_LINES_V3.csv", "LA_EXPORT_USABLE_V3.csv"):
    print(f); print((D / f).read_text()[:1400])
