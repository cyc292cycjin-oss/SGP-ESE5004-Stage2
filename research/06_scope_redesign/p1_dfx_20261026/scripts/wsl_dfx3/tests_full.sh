#!/bin/bash
# DFX v3 F6.1: the full test suite in the worktree (no Gurobi licence in the environment: GRB_LICENSE_FILE removed; no real solve may be running).
set -u
WT=/home/jin/wt_dfx_v3_20261026; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
cd "$WT" || exit 1
n=$(ps -eo args= | grep -E '[s]2_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '); [ "$n" = 0 ] || { echo "REAL SOLVE RUNNING ($n)"; exit 4; }
LOG=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/tests; mkdir -p $LOG
t0=$(date +%s)
env -u GRB_LICENSE_FILE $PY -m pytest -q -p no:cacheprovider tests > $LOG/full.log 2>&1
rc=$?
echo "FULL_SUITE_EXIT=$rc seconds=$(( $(date +%s) - t0 ))"
grep -E "^(FAILED|ERROR)|passed|failed" $LOG/full.log | tail -30
