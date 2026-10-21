#!/bin/bash
# M12b: mirror work/p1_m12b_20261021 into the repo deliverable folder, stage, commit with /home/jin/m12b_msg.txt
set -e
cd /home/jin/wt_m12_20261021
[ "$(git branch --show-current)" = "codex/m12b-loo-local-20261021" ] || { echo "wrong branch"; exit 2; }
SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12b_20261021
DST=research/06_scope_redesign/p1_m12b_20261021
mkdir -p "$DST"
rsync -a --exclude '*.zip' "$SRC"/ "$DST"/
git add -A scripts_project tests research/STAGE2_PROJECT_LEDGER.md; git add -f "$DST"
if [ -f /home/jin/m12b_force.txt ]; then
  while read -r p; do [ -n "$p" ] && [ -e "$p" ] && git add -f "$p"; done < /home/jin/m12b_force.txt
fi
git status --short | head -40
git commit -q -F /home/jin/m12b_msg.txt
git log --oneline -1
