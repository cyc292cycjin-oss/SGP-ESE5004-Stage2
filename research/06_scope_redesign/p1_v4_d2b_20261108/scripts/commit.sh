#!/bin/bash
# D2b: mirror the delivery folder into the repository and commit with the message file $1 (written beforehand; hooks are not skipped, no hooksPath
# override, no --no-verify). $2..: extra repository paths to add. Paths under research_inputs/ and research/ are force-added (csv / json there are
# ignored by .gitignore); every other path is added without -f so that __pycache__ / *.pyc stay ignored.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2b_20261108; R=/home/jin/wt_v4_d2b
MSG=$1; shift
[ -s "$MSG" ] || { echo "REFUSED: message file $MSG missing or empty"; exit 2; }
bash $W/scripts/sync.sh
cd $R || exit 1
git reset -q
git add -f research/06_scope_redesign/p1_v4_d2b_20261108
for p in "$@"; do
  case "$p" in research_inputs/*|research/*) git add -f "$p" ;; *) git add "$p" ;; esac
done
git status --short | grep -E '__pycache__|\.pyc$' && { echo "REFUSED: pyc staged"; exit 3; }
for i in 1 2 3 4 5; do
  git commit -q -F "$MSG" && break
  [ -e "$(git rev-parse --git-dir)/index.lock" ] || exit 3
  sleep 30
done
git log -1 --format='%H %s'
git status --short | head -5
