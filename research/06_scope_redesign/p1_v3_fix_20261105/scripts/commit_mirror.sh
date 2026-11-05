#!/bin/bash
# V3.1: mirror the work folder into the worktree (research/06_scope_redesign/p1_v3_fix_20261105), append the ledger entry once, stage the listed extra paths,
# commit with the message file (no push here). usage: commit_mirror.sh <msg file> [extra path ...]
set -eu
MSG=$1; shift
WORK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105
WT=/home/jin/wt_v3_fix
DST=$WT/research/06_scope_redesign/p1_v3_fix_20261105
cd "$WT"
[ "$(git rev-parse --abbrev-ref HEAD)" = codex/v3-fix-20261105 ] || { echo "wrong branch"; exit 2; }
find "$WORK/scripts" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
mkdir -p "$DST"
rsync -a --delete --exclude '__pycache__' --exclude 'draft/' "$WORK/" "$DST/"
if [ -f "$WORK/scripts/ledger_entry.md" ]; then
  grep -q "^### V3.1 FIX（第 195 项" research/STAGE2_PROJECT_LEDGER.md || cat "$WORK/scripts/ledger_entry.md" >> research/STAGE2_PROJECT_LEDGER.md
  git add research/STAGE2_PROJECT_LEDGER.md
fi
git add -f research/06_scope_redesign/p1_v3_fix_20261105
[ $# -eq 0 ] || git add -- "$@"
echo "== staged"; git diff --cached --stat | tail -8
git -c core.autocrlf=false commit -q -F "$MSG"
git log -1 --format='%H %s' | cut -c1-140
git status --short --untracked-files=no | head -5
