"""V3.1 definition = the v3 HPC definition with a new name / note and run_dirs (runs/batch5, runs/smoke56_v31); every other key byte-equal (asserted)."""
import json
import sys
from pathlib import Path

d = Path(sys.argv[1])
src = d / "BATCH_DEF_2920x3h_v3hpc.json"; dst = d / "BATCH_DEF_2920x3h_v31hpc.json"
if dst.exists():
    raise SystemExit(f"{dst} exists - never overwritten")
v3 = json.loads(src.read_text(encoding="utf-8"))
new = dict(v3)
new["name"] = ("V3.1 2920x3h formal batch on NUS Atlas (PBS Pro): F1 / F2 main, F3 / F4 EV fleet x0.5 (decisions 160-165, 172-173, 179, 180, 182, 186, 187; S-A shipping; "
               "decision 195: bunker net-zero written per metering flow)")
new["note"] = ("Copied into the v3.1 HPC package as BATCH_DEF.json (RUN_PLAN_HPC_V3.md section 15). V3.1 (decision 195, 2026-11-05) changes the code only: the bunker "
               "net-zero hook writes every metering flow into 'co2 bunkers ASEAN' = 0 per snapshot instead of the zero-slack final-level row that Gurobi's presolve "
               "declared INF_OR_UNBD on the 2920x3h windows (work/p1_v3_diag_20261105). Networks, limits (REGISTERED 2026-11-04, RUN_PLAN_HPC_V3.md section 14), PBS jobs, "
               "resources, smoke expectations and acceptance are those of the v3 definition BATCH_DEF_2920x3h_v3hpc.json; new run folders runs/batch5 (formal; runs/batch4 on "
               "the HPC is the halted v3 batch, kept untouched) and runs/smoke56_v31 (smoke).")
new["run_dirs"] = {"formal": "runs/batch5", "smoke56": "runs/smoke56_v31", "build_only": "runs/build_only_f1"}
for k in v3:
    if k not in ("name", "note"):
        assert json.dumps(new[k], sort_keys=True) == json.dumps(v3[k], sort_keys=True), k
dst.write_text(json.dumps(new, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("written", dst, "keys", list(new))
