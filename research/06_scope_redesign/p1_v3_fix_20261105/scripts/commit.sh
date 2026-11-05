#!/bin/bash
# Commit the listed paths of the fix worktree with a message file: bash commit.sh <msg file> <path>...
set -eu
MSG=$1; shift
cd /home/jin/wt_v3_fix
[ "$(git rev-parse --abbrev-ref HEAD)" = codex/v3-fix-20261105 ] || { echo "wrong branch"; exit 2; }
git add -- "$@"
git -c core.autocrlf=false commit -q -F "$MSG"
git log -1 --format='%H %s' | cut -c1-140
git status --short | head -20
