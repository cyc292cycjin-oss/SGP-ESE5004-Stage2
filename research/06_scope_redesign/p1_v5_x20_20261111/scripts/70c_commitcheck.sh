#!/bin/bash
# 只读：最近一次提交的文件范围核对（台账是否在内；scripts_project / configs / research_inputs / tests 是否无改动）与 worktree 状态
cd /home/jin/wt_v5_x20 || exit 1
git show --stat --format='%H %s' HEAD -- research/STAGE2_PROJECT_LEDGER.md | head -5
echo "code/config/input/test files changed in HEAD: $(git diff --name-only HEAD~1 HEAD -- scripts_project configs research_inputs tests | wc -l)"
echo "files in HEAD commit: $(git diff --name-only HEAD~1 HEAD | wc -l)"
git status --short | head -5
