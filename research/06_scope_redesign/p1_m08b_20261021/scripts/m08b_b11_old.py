"""M08b: run gate_b11_completeness on the S4M-3 networks (before the corrections) to see whether its failure pre-dates M08b (read-only)."""
import logging
import sys
from pathlib import Path

import pypsa

sys.path.insert(0, "/home/jin/wt_m08b_20261021/scripts_project")
from phase4_static import config   # noqa: E402
from v5.v5_gates import gate_b11_completeness, gate_b11_supply_routes   # noqa: E402

logging.getLogger("pypsa").setLevel(logging.ERROR)
B = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4m/s4m3/builds")
for s in ["integrated", "disconnected"]:
    n = pypsa.Network(B / s / f"{s}_2920_3h_unsolved.nc"); cfg = config(Path("/home/jin/wt_m08b_20261021"), s)
    a = gate_b11_completeness(n, cfg); b = gate_b11_supply_routes(n, cfg)
    by = {}
    for m in a["missing"]:
        by[m["carrier"]] = by.get(m["carrier"], 0) + 1
    print(s, "S4M-3 B11_completeness passed:", a["passed"], "missing_count:", a["missing_count"], "first-50 by carrier:", by, "| supply_routes passed:", b["passed"])
