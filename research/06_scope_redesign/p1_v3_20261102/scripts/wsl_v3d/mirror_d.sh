#!/bin/bash
# V3 supplement 07: copy the deliverables of this supplement to work/p1_v3_20261102/ (the review side reads them there), compare, check the instruction hashes and the other V3_* mirrors.
set -e
W=/home/jin/wt_v3_20261102; D=$W/research/06_scope_redesign/p1_v3_20261102; WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102
F="V3_REPORT_SUPPLEMENT07.md V3_RULES.md V3_PROGRESS.md V3_DEPLOY_FILES.md RUN_PLAN_V3.md RUN_PLAN_SCREEN_V3.md"
for f in $F; do [ -f "$D/$f" ] && cp "$D/$f" "$WORK/$f"; done
cp "$D/batch_def/BATCH_DEF_365x24h_dmax.json" "$WORK/batch_def/"
mkdir -p "$WORK/evidence/dmax"; cp -r "$D/evidence/dmax/." "$WORK/evidence/dmax/"
cd "$WORK"; sha256sum -c V3_INSTRUCTION_SHA256.txt V3_SCREEN_INSTRUCTION_SHA256.txt V3_SCREEN_UNATTENDED_SHA256.txt
for f in $F batch_def/BATCH_DEF_365x24h_dmax.json; do [ -f "$D/$f" ] && cmp "$D/$f" "$WORK/$f" && echo "same $f"; done
diff -rq "$D/evidence/dmax" "$WORK/evidence/dmax" && echo "same evidence/dmax"
for f in "$D"/V3_*.md; do b=$(basename "$f"); [ -f "$WORK/$b" ] && { cmp -s "$f" "$WORK/$b" || echo "MIRROR DIFFERS: $b"; }; done
sha256sum V3_REVIEW_DECISIONS_EVDIAG.md
cd "$W"; git log --oneline -1 | cut -c1-90; git status --short | wc -l
