import json, re, sys
from pathlib import Path
for run in sys.argv[1:]:
    for rid in ("integrated", "no_new_xb"):
        d = Path(run) / rid; r = json.loads((d / "SOLVE_RECEIPT.json").read_text())
        log = (d / "gurobi.linopy.log").read_text(errors="ignore") if (d / "gurobi.linopy.log").exists() else ""
        m = re.findall(r"Barrier performed (\d+) iterations in ([\d.]+) seconds", log) or re.findall(r"Barrier solved model in (\d+) iterations and ([\d.]+) seconds", log)
        print(Path(run).name, rid, r.get("termination_condition"), r.get("objective"), r.get("solve_seconds"), m[-1] if m else None, (r.get("lp") or {}).get("num_row"), (r.get("lp") or {}).get("num_col"))
