#!/bin/bash
# V3 supplement 06: run one read-only diagnosis script with the project python (no solver); usage: run.sh <script.py> [args]
cd /home/jin/wt_v3_20261102 || exit 2
export PYTHONHASHSEED=0 PYTHONWARNINGS=ignore
S=$(date +%s)
/home/jin/miniforge3/envs/pypsa-earth/bin/python "$@" 2>&1 | grep -v -E "Warning|warnings.warn|FutureWarning"
echo "ELAPSED_S $(( $(date +%s) - S ))"
