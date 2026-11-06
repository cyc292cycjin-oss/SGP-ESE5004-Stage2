#!/bin/bash
# D1: mirror the delivery folder into the repository and commit with the message file $1 (written beforehand; hooks are not skipped, no hooksPath
# override). $2..: extra repository paths to add (force-add: csv / json under research_inputs are ignored by .gitignore).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d1_20261107; R=/home/jin/wt_v4_d1
MSG=$1; shift
[ -s "$MSG" ] || { echo "REFUSED: message file $MSG missing or empty"; exit 2; }
bash $W/scripts/sync.sh
cd $R || exit 1
find . -name __pycache__ -type d -path './scripts_project/*' -prune -o -name __pycache__ -type d -path './tests/*' -prune > /dev/null
git add -f research/06_scope_redesign/p1_v4_d1_20261107
for p in "$@"; do git add -f "$p"; done
git status --short | grep -E '__pycache__|\.pyc$' && { echo "REFUSED: pyc staged"; exit 3; }
for i in 1 2 3 4 5; do
  git commit -q -F "$MSG" && break
  [ -e "$(git rev-parse --git-dir)/index.lock" ] || exit 3
  sleep 30
done
git log -1 --format='%H %s'
