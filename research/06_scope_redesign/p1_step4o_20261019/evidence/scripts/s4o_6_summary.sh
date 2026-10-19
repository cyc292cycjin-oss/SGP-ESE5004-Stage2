#!/bin/bash
# S4O-6 batch summary (read only, WSL project Python): per-run table, B6 (this batch's disconnected - pilot integrated), NZE - integrated, L23 comparison
# usage: bash s4o_6_summary.sh <run timestamp> <out stem>
set -u
TS=${1:?run timestamp}; STEM=${2:-S4O6_BATCH_SUMMARY}
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
C=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019/cloud_results/$TS
PL=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/cloud_results/20261019T072454Z_5125/unpacked/s4n_pilot_light_20261019T072454Z_5125
BD=$C/top; [ -d $BD ] || BD=$C/none
$PY $RM/research/06_scope_redesign/p1_step4o_20261019/evidence/scripts/s4o_6_summary.py $C/full/unpacked $PL \
  $RM/research/06_scope_redesign/p1_l23_run1_20261019/evidence/c9_summary/L23_C9_SUMMARY.json $BD $C/$STEM.json $C/$STEM.md
