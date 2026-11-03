#!/bin/bash
# V3 supplement 07: mirror the session scripts into the branch, refuse a licence-like string, stage ONLY the given paths (plus the script mirror), commit, print the head.
# usage: commit_d.sh <message file> <path> [<path> ...]   (paths relative to the worktree; ignored csv / json are force-added)
set -e
W=/home/jin/wt_v3_20261102; D=research/06_scope_redesign/p1_v3_20261102
MSG=$1; shift
cd "$W"
mkdir -p "$D/scripts/wsl_v3d"
cp /home/jin/v3d/*.py /home/jin/v3d/*.sh "$D/scripts/wsl_v3d/" 2>/dev/null || true
P="WLS""ACCESSID|WLS""SECRET|LICENSE""ID|BEGIN (RSA|OPENSSH) PRIVATE"" KEY"
if grep -rIlE "$P" "$@" "$D/scripts/wsl_v3d" 2>/dev/null; then echo "LEAK SUSPECT"; exit 3; fi
git add -f "$@" "$D/scripts/wsl_v3d"
echo "== staged"; git diff --cached --stat | tail -30
echo "== left unstaged (tracked)"; git status --short --untracked-files=no | grep -v '^[MADR] ' | head -10
git commit -q -F "$MSG"
git log --oneline -1 | cut -c1-120
