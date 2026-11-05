#!/bin/bash
set -e
W=/home/jin/wt_v31_review
SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105
DST=$W/research/06_scope_redesign/p1_v3_fix_20261105
cd "$W"
git status --porcelain | head -5
mkdir -p "$DST/review_v31"
cp "$SRC/V31_FABLE_REVIEW.md" "$DST/V31_FABLE_REVIEW.md"
cp -r "$SRC/review_v31/scripts" "$SRC/review_v31/evidence" "$DST/review_v31/"
cp /home/jin/v31rev/commit.sh "$DST/review_v31/scripts/commit.sh"
git add "$DST/V31_FABLE_REVIEW.md" "$DST/review_v31"
git status --porcelain | wc -l
git commit -q -F /home/jin/v31rev/msg.txt
git log -1 --format="%H %cI %s"
git push -q -u origin codex/v31-review-20261105 2>&1 | tail -3
git rev-parse --short=8 HEAD origin/codex/v31-review-20261105
