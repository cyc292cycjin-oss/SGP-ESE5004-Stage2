#!/bin/bash
# W14: mirror the delivery folder into the repository and commit with the message file $1 (written beforehand; hooks are not skipped, no hooksPath
# override, no --no-verify). Only the W14 folder research/06_scope_redesign/p1_v4_w14_20261109 is added (force: csv / json there are ignored by
# .gitignore); model code, inputs, configuration and registry are never added (instruction section 0: not changed).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w14_20261109; R=/home/jin/wt_v4_w14
MSG=$1
[ -s "$MSG" ] || { echo "REFUSED: message file $MSG missing or empty"; exit 2; }
bash $W/scripts/sync.sh
cd $R || exit 1
D=$(git status --porcelain --untracked-files=no -- . ':!research/06_scope_redesign/p1_v4_w14_20261109' | wc -l)
[ "$D" = 0 ] || { echo "REFUSED: $D tracked change(s) outside the W14 folder"; git status --short | head; exit 2; }
git reset -q
git add -f research/06_scope_redesign/p1_v4_w14_20261109
git status --short | grep -E '__pycache__|\.pyc$' && { echo "REFUSED: pyc staged"; exit 3; }
git status --short | grep -vE '^[AMD][ MD] research/06_scope_redesign/p1_v4_w14_20261109/|^\?\?' && { echo "REFUSED: something outside the W14 folder is staged"; exit 3; }
for i in 1 2 3 4 5; do
  git commit -q -F "$MSG" && break
  [ -e "$(git rev-parse --git-common-dir)/index.lock" ] || exit 3
  sleep 30
done
git log -1 --format='%H %s'
git status --short | head -5
