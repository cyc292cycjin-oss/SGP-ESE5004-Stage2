#!/bin/bash
# HPR: the HPR + B4P stand-in test files in ONE pytest process (no Gurobi licence in the environment; no real solve may be running).
set -u
WT=/home/jin/wt_hpr_20261027; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
cd "$WT" || exit 1
n=$(ps -eo args= | grep -E '[s]2_solve\.py|[b]4_split_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '); [ "$n" = 0 ] || { echo "REAL SOLVE RUNNING ($n)"; exit 4; }
LOG=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/hpr/tests; mkdir -p $LOG
t0=$(date +%s)
env -u GRB_LICENSE_FILE $PY -m pytest -q -p no:cacheprovider tests/research/test_hpr_two_jobs.py tests/research/test_b4p_batch4.py "$@" > $LOG/hpr_b4p.log 2>&1
rc=$?
echo "HPR_B4P_EXIT=$rc seconds=$(( $(date +%s) - t0 ))"
grep -E "^(FAILED|ERROR)|passed|failed" $LOG/hpr_b4p.log | tail -20
echo HPR_B4P_DONE >> $LOG/hpr_b4p.log
