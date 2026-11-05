#!/bin/bash
# V3 DIAG: mirror the work folder into the worktree, append the ledger entry once, commit with the message file (no push here).
set -eu
WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_diag_20261105
WT=/home/jin/wt_v3_diag
DST=$WT/research/06_scope_redesign/p1_v3_diag_20261105
rm -rf "$WORK/scripts/__pycache__"
mkdir -p "$DST"
rsync -a --delete --exclude '__pycache__' "$WORK/" "$DST/"
cd "$WT"
grep -q "^### V3 DIAG（第 194 项" research/STAGE2_PROJECT_LEDGER.md || cat "$WORK/scripts/ledger_entry.md" >> research/STAGE2_PROJECT_LEDGER.md
git add -f research/06_scope_redesign/p1_v3_diag_20261105
git add research/STAGE2_PROJECT_LEDGER.md
echo "== staged"; git diff --cached --stat | tail -5
echo "== ignored-but-staged check"; git diff --cached --name-only | grep -cE '\.(csv|log|nc)$' || true
git commit -q -F "$WORK/scripts/commit_msg.txt"
git log -1 --format='%H %s'
git status --short | head -5
