#!/bin/bash
# HPR H-P5: the full test suite in the worktree at the final code commit (no Gurobi licence in the environment; no real solve may be running).
set -u
WT=/home/jin/wt_hpr_20261027; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
cd "$WT" || exit 1
n=$(ps -eo args= | grep -E '[s]2_solve\.py|[b]4_split_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '); [ "$n" = 0 ] || { echo "REAL SOLVE RUNNING ($n)"; exit 4; }
LOG=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/hpr/tests; mkdir -p $LOG
echo "FULL_SUITE_COMMIT=$(git rev-parse HEAD) dirty=$(git status --porcelain --untracked-files=no | wc -l)" > $LOG/full_commit.txt
t0=$(date +%s)
env -u GRB_LICENSE_FILE $PY -m pytest -q -p no:cacheprovider tests > $LOG/full.log 2>&1
rc=$?
echo "FULL_SUITE_EXIT=$rc seconds=$(( $(date +%s) - t0 ))" | tee -a $LOG/full_commit.txt
grep -E "^(FAILED|ERROR)|passed|failed" $LOG/full.log | tail -30
echo FULL_DONE >> $LOG/full.log
