#!/bin/bash
# W08: timing of the R0 solve (no licence lines printed: scrubbed log only)
D=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/smoke56/v31_F1
grep -iE "barrier solved|presolve time|optimal objective|solved in|crossover|ordering time" $D/GUROBI_LOG_SCRUBBED.txt | head
/home/jin/miniforge3/envs/pypsa-earth/bin/python - <<EOF
import json
r = json.load(open("$D/SOLVE_RECEIPT.json"))
print("solve_seconds", r["solve_seconds"], "receipt span", r["finished_epoch"] - r["started_epoch"], r["gurobi_log_stats"]["lines"]["barrier"])
EOF
grep -E "^ *(Elapsed|Maximum resident|Percent of CPU)" $D/solve.err
