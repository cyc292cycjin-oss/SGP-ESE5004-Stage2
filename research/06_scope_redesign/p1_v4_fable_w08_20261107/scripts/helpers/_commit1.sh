#!/bin/bash
# Fable W08 review: mirror the work folder into the review branch and commit (stage 3). No hooks skipped. usage: _commit1.sh <msg file name under scripts/helpers>
set -u
WT=/home/jin/wt_v4_fable; SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_fable_w08_20261107; DST=$WT/research/06_scope_redesign/p1_v4_fable_w08_20261107
MSG=${1:-_commit_msg1.txt}
mkdir -p $DST
rsync -a --delete --exclude "*.zip" --exclude "__pycache__" --exclude ".pytest_cache" $SRC/ $DST/
cd $WT || exit 1
git add -f research/06_scope_redesign/p1_v4_fable_w08_20261107
echo "== staged =="; git status --short | head -60; echo "staged files: $(git diff --cached --name-only | wc -l)"
echo "== untracked / modified outside the delivery folder (must be empty) =="; git status --short | grep -v "research/06_scope_redesign/p1_v4_fable_w08_20261107" | head
git commit -q -F $SRC/scripts/helpers/$MSG && echo "COMMIT $(git rev-parse HEAD)" || { echo "COMMIT FAILED"; exit 1; }
git log --oneline -3
