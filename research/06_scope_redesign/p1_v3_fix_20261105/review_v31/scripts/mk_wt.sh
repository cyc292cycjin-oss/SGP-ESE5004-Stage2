#!/bin/bash
set -u
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
cd "$R" || exit 1
git fetch origin codex/v3-fix-20261105 2>&1 | tail -2
echo "--- head of codex/v3-fix-20261105 (local / remote) ---"
git rev-parse --short=8 codex/v3-fix-20261105 2>/dev/null
git rev-parse --short=8 origin/codex/v3-fix-20261105 2>/dev/null
git log --oneline -6 1117a07f
echo "--- package commit d3b9a3bc ---"
git log --oneline -1 d3b9a3bc
git merge-base --is-ancestor d3b9a3bc 1117a07f && echo "d3b9a3bc is ancestor of 1117a07f"
if [ -d /home/jin/wt_v31_review ]; then echo "worktree exists"; else
  git worktree add -b codex/v31-review-20261105 /home/jin/wt_v31_review 1117a07f 2>&1 | tail -3
fi
cd /home/jin/wt_v31_review && git rev-parse --short=8 HEAD && git status -sb | head -3
echo "--- fix branch diff stat vs v3 package commit 7d22dda1 ---"
git -C "$R" diff --stat 7d22dda1 1117a07f | tail -25
echo "--- diff stat d3b9a3bc..1117a07f ---"
git -C "$R" diff --stat d3b9a3bc 1117a07f | tail -15
