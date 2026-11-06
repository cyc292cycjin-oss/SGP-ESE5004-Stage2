#!/bin/bash
# W08: repository checkpoints for a switch set and comparison with the reference engine.
# usage: run_cp.sh <label> <reference scratch name: main|iid|i2chk> <steps, e.g. S0,S1,S2> [v4_industry --set overrides ...]
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106; R=/home/jin/wt_v4_w08; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
label=$1; ref=$2; steps=$3; shift 3
export PYTHONHASHSEED=0
OUT=/home/jin/v4w08/cp_$label; mkdir -p $OUT
cd $R || exit 1
sets=(); for x in "$@"; do sets+=(--set "$x"); done
$PY scripts_project/v4_industry.py --checkpoints $OUT --steps $steps --work /home/jin/v4w08/work_$label "${sets[@]}" > $OUT/run.log 2>&1 || { tail -30 $OUT/run.log; exit 1; }
cat $OUT/run.log
cd $W && $PY scripts/w08_checkpoints.py $OUT /home/jin/v4w08/ref_$ref/results $label --steps $steps
