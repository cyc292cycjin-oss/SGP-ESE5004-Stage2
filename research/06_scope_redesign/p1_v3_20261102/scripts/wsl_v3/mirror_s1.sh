#!/bin/bash
# V3 supplement 01: mirror the deliverables to work/ (the two instruction files stay untouched), compare, check the instruction hashes
set -e
W=/home/jin/wt_v3_20261102; D=$W/research/06_scope_redesign/p1_v3_20261102; WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102
F="V3_REPORT_SUPPLEMENT01.md RUN_PLAN_V3.md V3_RULES.md V3_PROGRESS.md V3_DEPLOY_FILES.md V3_X1_STOP_NOTE.md V3_REPORT_PHASE3.md"
for f in $F; do cp "$D/$f" "$WORK/$f"; done
cp -r "$D/evidence/." "$WORK/evidence/"; cp -r "$D/batch_def" "$WORK/"
cd "$WORK"; sha256sum -c V3_INSTRUCTION_SHA256.txt
for f in $F; do cmp "$D/$f" "$WORK/$f"; done; diff -rq "$D/evidence" "$WORK/evidence" | head -5; echo mirrored
cd "$W"; git log --oneline -2 | cut -c1-90; git status --short | wc -l
