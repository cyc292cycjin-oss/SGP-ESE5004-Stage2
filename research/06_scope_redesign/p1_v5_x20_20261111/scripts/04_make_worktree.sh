#!/bin/bash
# X20：从 W14 包 COMMIT 26c2e47d 新建分支 asean/v5-x20-20261111 与稀疏检出 worktree（A 段只放本步目录）
set -eu
REPO=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
WT=/home/jin/wt_v5_x20
BR=asean/v5-x20-20261111
C=26c2e47d025fdd4e46cb278718d93aeddabbe984
STEP=research/06_scope_redesign/p1_v5_x20_20261111
cd "$REPO"
echo "== remote check"; timeout 60 git ls-remote origin "refs/heads/$BR" || echo "ls-remote failed (exit $?)"
if git show-ref --verify --quiet "refs/heads/$BR"; then echo "branch exists, stop"; exit 3; fi
if [ -e "$WT" ]; then echo "worktree path exists, stop"; exit 3; fi
git worktree add --no-checkout -b "$BR" "$WT" "$C"
cd "$WT"
git sparse-checkout set --cone "$STEP"
git checkout "$BR" 2>&1 || true
git read-tree -mu HEAD
echo "== head"; git rev-parse HEAD; git branch --show-current
echo "== status"; git status --short | head; echo "(status lines: $(git status --short | wc -l))"
echo "== sparse list"; git sparse-checkout list
echo "== files on disk"; find . -path ./.git -prune -o -type f -print | wc -l
du -sh "$WT"
echo "== shared config now"; git config --show-origin --get-regexp "extensions|sparse" || true
echo "== hooks dir"; ls "$(git rev-parse --git-common-dir)/hooks" | grep -v sample || echo "no active hooks"
