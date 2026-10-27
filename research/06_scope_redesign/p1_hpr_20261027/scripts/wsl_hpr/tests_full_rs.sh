#!/bin/bash
# HPR H-P5: the full suite once more with the skip reasons (-rs) so that every skipped test can be listed; no Gurobi licence in the environment.
set -u
WT=/home/jin/wt_hpr_20261027; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
cd "$WT" || exit 1
n=$(ps -eo args= | grep -E '[s]2_solve\.py|[b]4_split_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '); [ "$n" = 0 ] || { echo "REAL SOLVE RUNNING ($n)"; exit 4; }
LOG=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/hpr/tests; mkdir -p $LOG
echo "FULL_RS_COMMIT=$(git rev-parse HEAD) dirty=$(git status --porcelain --untracked-files=no | wc -l)" > $LOG/full_rs_commit.txt
t0=$(date +%s)
env -u GRB_LICENSE_FILE $PY -m pytest -q -rs -p no:cacheprovider tests > $LOG/full_rs.log 2>&1
rc=$?
echo "FULL_RS_EXIT=$rc seconds=$(( $(date +%s) - t0 ))" | tee -a $LOG/full_rs_commit.txt
grep -E "passed|failed" $LOG/full_rs.log | tail -1
grep -E "^SKIPPED" $LOG/full_rs.log | sed -E "s/^SKIPPED \[([0-9]+)\] ([^:]+):[0-9]+: (.*)/\2 | \1 | \3/" | sort | uniq -c | sort -rn > $LOG/full_rs_skips.txt
cp $LOG/full_rs.log $LOG/full_rs_commit.txt $LOG/full_rs_skips.txt $WT/research/06_scope_redesign/p1_hpr_20261027/evidence/tests/ 2>/dev/null
wc -l < $LOG/full_rs_skips.txt
echo FULL_RS_DONE >> $LOG/full_rs.log
