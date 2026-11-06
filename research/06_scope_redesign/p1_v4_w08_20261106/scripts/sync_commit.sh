#!/bin/bash
# W08: mirror the delivery folder into the repository (research/06_scope_redesign/p1_v4_w08_20261106/, zip files excluded) and commit with the
# message file given as $1 (written beforehand; hooks are not skipped). Optional $2..: extra repository paths to add (force-add, csv are ignored).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106; R=/home/jin/wt_v4_w08; D=$R/research/06_scope_redesign/p1_v4_w08_20261106
MSG=$1; shift
[ -s "$MSG" ] || { echo "REFUSED: message file $MSG missing or empty"; exit 2; }
mkdir -p $D
rsync -a --delete --exclude '*.zip' --exclude '__pycache__' --exclude 'msg_*.txt' $W/ $D/
cd $R || exit 1
git add -f research/06_scope_redesign/p1_v4_w08_20261106
for p in "$@"; do git add -f "$p"; done
for i in 1 2 3 4 5; do
  git commit -q -F "$MSG" && break
  [ -e .git/index.lock ] || [ -e "$(git rev-parse --git-dir)/index.lock" ] || exit 3
  sleep 30
done
git log -1 --format='%H %s'
