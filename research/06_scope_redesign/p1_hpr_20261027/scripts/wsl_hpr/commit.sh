#!/bin/bash
# HPR commit helper: bash /home/jin/hpr/commit.sh <message file> [extra paths...]
# Adds the deliverable folder, the code / config / test paths and the B4P / DFX package sources changed by HPR, mirrors the WSL helper scripts
# into the deliverable folder, then commits with the message file. Never pushes.
set -u
WT=/home/jin/wt_hpr_20261027
MSG=${1:?message file}; shift
cd "$WT" || exit 1
[ "$(git branch --show-current)" = codex/hpr-20261027 ] || { echo "WRONG BRANCH"; exit 2; }
D=research/06_scope_redesign/p1_hpr_20261027
mkdir -p $D/scripts/wsl_hpr
cp /home/jin/hpr/*.sh /home/jin/hpr/*.py $D/scripts/wsl_hpr/ 2>/dev/null
rm -rf $D/scripts/wsl_hpr/__pycache__
git add -A $D scripts_project configs tests research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4 research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx "$@"
git status --short | head -60
git commit -q -F "$MSG" && git log --oneline -1
