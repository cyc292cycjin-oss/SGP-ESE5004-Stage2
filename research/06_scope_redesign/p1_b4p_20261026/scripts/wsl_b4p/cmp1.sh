#!/bin/bash
# compare two solve folders: bash cmp1.sh <A> <B> <label>   (A/B = tags under results_project/b4p/solves or absolute paths)
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026/evidence
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
A=$1; B=$2; L=${3:?label}
case "$A" in /*) ;; *) A=$R/solves/$A;; esac
case "$B" in /*) ;; *) B=$R/solves/$B;; esac
mkdir -p $E/compare
env -u GRB_LICENSE_FILE $PY /home/jin/b4p/compare_solves.py "$A" "$B" "$E/compare/$L.json" --label "$L"
echo "exit $?"
