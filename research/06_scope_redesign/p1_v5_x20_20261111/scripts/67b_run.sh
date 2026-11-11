#!/bin/bash
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
export PYTHONHASHSEED=0
AV=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo); echo "MemAvailable_MiB $AV"; [ "$AV" -lt 4608 ] && { echo GATE REFUSED; exit 3; }
$PY $D/scripts/${1:-67b_diag.py} 2>&1 | grep -v -e Warning -e PROJ -e pypsa.io > $D/logs/${1:-67b_diag.py}.log; cat $D/logs/${1:-67b_diag.py}.log
