#!/bin/bash
# M12b 第 1 节：在 M12 worktree 新建分支并普通 merge M08b 补充 01 分支头（不 rebase、不 force-push）
set -u
cd /home/jin/wt_m12_20261021 || exit 1
echo "=== status before"; git status --short | head; git branch --show-current; git rev-parse HEAD
git fetch origin codex/m08b-demand-20261021 codex/m12-allocation-20261021 2>&1 | tail -2
echo "origin m08b: $(git rev-parse origin/codex/m08b-demand-20261021)  local m08b: $(git rev-parse codex/m08b-demand-20261021)"
echo "origin m12:  $(git rev-parse origin/codex/m12-allocation-20261021)  local m12: $(git rev-parse codex/m12-allocation-20261021)"
echo "merge-base: $(git merge-base HEAD codex/m08b-demand-20261021)"
if git show-ref --verify --quiet refs/heads/codex/m12b-loo-local-20261021; then echo "BRANCH EXISTS"; exit 2; fi
git switch -c codex/m12b-loo-local-20261021 || exit 3
git merge --no-ff --no-commit codex/m08b-demand-20261021 > /home/jin/m12b_merge.out 2>&1; rc=$?
cat /home/jin/m12b_merge.out
echo "merge rc=$rc"
echo "=== conflicts"; git diff --name-only --diff-filter=U
echo "=== staged summary"; git diff --cached --stat | tail -5
