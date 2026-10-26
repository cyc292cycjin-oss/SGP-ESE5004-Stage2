#!/bin/bash
# DFX v3 F5.3 / F5.4: demand review chain (v1 tables from git -> D1 v1 / v2 -> diff -> bridge -> per-capita) and the first-order prediction. No solve.
set -u
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/scripts
export PYTHONHASHSEED=0
L=$MAIN/results_project/dfx_v3/review; mkdir -p $L
cd $WT || exit 1
for step in "tables" "d1 --tag v1" "d1 --tag v2" "diff" "bridge" "percap"; do
  name=$(echo "$step" | tr ' -' '__')
  $PY $S/dfx_demand_review.py $step > $L/$name.log 2>&1; echo "$step exit=$? $(grep -v -E 'UserWarning|warn\(' $L/$name.log | tail -1 | cut -c1-200)"
done
$PY $S/dfx_first_order.py > $L/first_order.log 2>&1; echo "first_order exit=$?"
grep -v -E "UserWarning|warn\(" $L/first_order.log | grep -E "ΔB6|ΔD =" | head -4
