#!/bin/bash
# Worktree state: status, diff stat, file modes of changed files. Read-only.
set -u
cd /home/jin/wt_v3_fix
git status --short
echo "== diff stat"; git diff --stat
echo "== mode changes"; git diff --summary | grep -E 'mode change' || echo "(none)"
echo "== head"; git log -1 --format='%H %s' | cut -c1-120
