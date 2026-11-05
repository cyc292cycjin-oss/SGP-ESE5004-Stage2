#!/bin/bash
# V3.1 fix (decision 195): create the fix worktree from the frozen package commit (instruction section 1.1).
set -eu
REPO=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
WT=/home/jin/wt_v3_fix
BR=codex/v3-fix-20261105
C=7d22dda112a3c18ed57e8c061d95e51915980417
cd "$REPO"
git cat-file -t "$C"
if [ -e "$WT" ]; then echo "WT_EXISTS $WT"; exit 3; fi
if git show-ref --verify --quiet "refs/heads/$BR"; then echo "BRANCH_EXISTS $BR"; exit 4; fi
git worktree add -b "$BR" "$WT" "$C"
cd "$WT"
git log -1 --format='%H %s'
echo "dirty=$(git status --porcelain | wc -l)"
echo "== hpc package COMMIT file"
cat /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3/COMMIT
echo "== worktrees"
git -C "$REPO" worktree list | grep -E 'wt_v3' || true
