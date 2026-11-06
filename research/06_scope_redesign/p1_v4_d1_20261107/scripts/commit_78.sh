#!/bin/bash
# D1: commit D1-7b (smoke results) then D1-8 (report, evidence, ledger draft, logs). Hooks not skipped.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d1_20261107; R=/home/jin/wt_v4_d1; D=research/06_scope_redesign/p1_v4_d1_20261107
bash $W/scripts/sync.sh
cd $R || exit 1
git add -f $D/SMOKE56_D1.md $D/tables/D1_SMOKE56_RESULTS.csv $D/evidence/D1_smoke56.json $D/scripts/d1_smoke_eval.py $D/batch_def/BATCH_DEF_2920x3h_v4hpc.json $D/PROGRESS.md
git commit -q -F $W/scripts/msg_d1_7b.txt && git log -1 --format='%H %s'
git add -f $D
git status --short | grep -E '__pycache__|\.pyc$' && { echo "REFUSED: pyc staged"; exit 3; }
git commit -q -F $W/scripts/msg_d1_8.txt && git log -1 --format='%H %s'
git status --short | head
