#!/bin/bash
# usage: commit.sh <message file> : stages the V3 HPC paths (force for the ignored csv / json tables), refuses a licence-like string, commits, prints the head
set -e
W=/home/jin/wt_v3_hpc; D=research/06_scope_redesign/p1_v3_20261102
cd "$W"
[ -s "$1" ] || { echo "message file $1 missing or empty"; exit 2; }
mkdir -p "$D/scripts/wsl_v3h"
cp /home/jin/v3h/*.py /home/jin/v3h/*.sh "$D/scripts/wsl_v3h/" 2>/dev/null || true
P="WLS""ACCESSID|WLS""SECRET|LICENSE""ID|BEGIN (RSA|OPENSSH) PRIVATE"" KEY"
if grep -rIlE --exclude=commit_p1.sh "$P" "$D" scripts_project configs tests research/06_scope_redesign/p1_hpr_20261027/hpc_package_src research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4 2>/dev/null; then echo "LEAK SUSPECT"; exit 3; fi
git add -A scripts_project configs tests
git add -f "$D"
git add -A research/06_scope_redesign/p1_hpr_20261027/hpc_package_src research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4
git add -u research_inputs/registry_v5
git status --short | cut -c1-100 | head -${2:-30}
git commit -q -F "$1"
git log --oneline -1 | cut -c1-140
