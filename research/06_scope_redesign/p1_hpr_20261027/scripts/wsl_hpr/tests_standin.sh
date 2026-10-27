#!/bin/bash
# HPR: the stand-in test files of every batch runner in ONE pytest process (no Gurobi licence in the environment; no real solve may be running).
set -u
WT=/home/jin/wt_hpr_20261027; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
cd "$WT" || exit 1
n=$(ps -eo args= | grep -E '[s]2_solve\.py|[b]4_split_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '); [ "$n" = 0 ] || { echo "REAL SOLVE RUNNING ($n)"; exit 4; }
LOG=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/hpr/tests; mkdir -p $LOG
t0=$(date +%s)
env -u GRB_LICENSE_FILE $PY -m pytest -q -p no:cacheprovider tests/research/test_hpr_two_jobs.py tests/research/test_b4p_batch4.py tests/research/test_b4p_split.py tests/research/test_b4p_paths.py \
  tests/research/test_dfx_runner.py tests/research/test_m10p_batch3.py tests/research/test_m10r_s1_modes.py tests/research/test_m10r_drill.py "$@" > $LOG/standin.log 2>&1
rc=$?
echo "STANDIN_EXIT=$rc seconds=$(( $(date +%s) - t0 ))"
grep -E "^(FAILED|ERROR)|passed|failed" $LOG/standin.log | tail -40
echo STANDIN_DONE >> $LOG/standin.log
