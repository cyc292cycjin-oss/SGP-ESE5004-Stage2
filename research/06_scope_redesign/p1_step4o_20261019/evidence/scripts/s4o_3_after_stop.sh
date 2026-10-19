#!/bin/bash
# S4O-3 stop record (read only apart from the STATUS line): no solver / runner process left; the objective difference against S4M-2 profile A
set -u
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; S=$RM/results_project/s4o/s4o3; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
echo "processes (runner / solver / C1): $(ps -eo cmd | grep -cE '[s]4o_3_run|[s]2_solve|[g]urobi_cl|[s]4o_c1_precision|[l]23_violation')"
ls $S/solves
echo "STOPPED_BY_OPERATOR:$(date -u +%Y-%m-%dT%H:%M:%SZ):S4O-3 point 4 - the integrated run is optimal but its objective differs from S4M-2 profile A by more than the decision-107 tolerance 1e-5 (standard not passed); the runner was ended during the 5-min gap BEFORE the disconnected solve started (no further solve, no retry); S4O-4 not entered" >> $S/STATUS.txt
echo "LAST_GUROBI_END:2026-10-19T12:57:18Z" >> $S/STATUS.txt
$PY - $S/solves/s4o_integrated/SOLVE_RECEIPT.json $RM/results_project/s4m/s4m2/solves/s4m_A_integrated/SOLVE_RECEIPT.json $RM/results_project/s4n/s4n_c2/solves/cal_integrated/SOLVE_RECEIPT.json <<'P'
import json, sys
n, a, c = (json.load(open(p)) for p in sys.argv[1:4])
print("objective S4O-3 integrated:", n["objective"], "profile", n.get("solver_profile"), n.get("solver_parameters"))
print("objective S4M-2 profile A :", a["objective"], " rel diff", (n["objective"] - a["objective"]) / a["objective"], " abs EUR", n["objective"] - a["objective"])
print("objective S4N C2 (thr 32) :", c["objective"], " rel diff vs A", (c["objective"] - a["objective"]) / a["objective"], " S4O vs C2", (n["objective"] - c["objective"]) / c["objective"])
P
tail -4 $S/STATUS.txt | cut -c1-200
