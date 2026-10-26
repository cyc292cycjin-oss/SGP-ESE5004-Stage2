#!/bin/bash
# DFX v3 commit helper: bash /home/jin/dfx3/commit.sh <message file> [extra paths...]
# Adds the deliverable folder, code, configs, tests and the force list (/home/jin/dfx3/force.txt: git-ignored csv / json inputs the registry cites),
# mirrors the WSL helper scripts into the deliverable folder, then commits with the message file. Never pushes.
set -u
WT=/home/jin/wt_dfx_v3_20261026
MSG=${1:?message file}; shift
cd "$WT" || exit 1
[ "$(git branch --show-current)" = codex/dfx-v3-20261026 ] || { echo "WRONG BRANCH"; exit 2; }
mkdir -p research/06_scope_redesign/p1_dfx_20261026/scripts/wsl_dfx3
cp /home/jin/dfx3/*.sh /home/jin/dfx3/*.py research/06_scope_redesign/p1_dfx_20261026/scripts/wsl_dfx3/ 2>/dev/null
cp -r /home/jin/dfx3/trace research/06_scope_redesign/p1_dfx_20261026/scripts/wsl_dfx3/ 2>/dev/null
rm -rf research/06_scope_redesign/p1_dfx_20261026/scripts/wsl_dfx3/trace/__pycache__ research/06_scope_redesign/p1_dfx_20261026/scripts/wsl_dfx3/__pycache__
git add -A research/06_scope_redesign/p1_dfx_20261026 scripts_project configs tests "$@"
if [ -f /home/jin/dfx3/force.txt ]; then
  while IFS= read -r f; do [ -n "$f" ] && for g in $f; do [ -e "$g" ] && git add -f "$g"; done; done < /home/jin/dfx3/force.txt
fi
git status --short | head -60
git commit -q -F "$MSG" && git log --oneline -1
