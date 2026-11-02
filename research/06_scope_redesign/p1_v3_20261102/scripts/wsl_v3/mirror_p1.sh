#!/bin/bash
# V3 phase 1: mirror the deliverables to work/ (the two instruction files stay untouched)
set -e
W=/home/jin/wt_v3_20261102; D=$W/research/06_scope_redesign/p1_v3_20261102; WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102
for f in V3_CODE_LOCATIONS.md V3_DATA_INTAKE.md V3_DESIGN.md V3_PROGRESS.md V3_REPORT_PHASE1.md; do cp "$D/$f" "$WORK/$f"; done
cp -r "$D/evidence" "$WORK/"
cd "$WORK"
sha256sum -c V3_INSTRUCTION_SHA256.txt
ls -la
for f in V3_CODE_LOCATIONS.md V3_DATA_INTAKE.md V3_DESIGN.md V3_PROGRESS.md V3_REPORT_PHASE1.md; do cmp "$D/$f" "$WORK/$f" && echo "same $f"; done
cd "$W"; git log --oneline -3 | cut -c1-70; git status --short | wc -l
