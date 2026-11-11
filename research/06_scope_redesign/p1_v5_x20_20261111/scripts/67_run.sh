#!/bin/bash
# 门控：可用 >= 4 GiB 且估计峰值（两张 2920 网络约 2.2 GiB）<= 可用的一半
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
AV=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo); echo "MemAvailable_MiB $AV"
if [ "$AV" -lt 4608 ]; then echo "GATE REFUSED: available < 4.5 GiB"; exit 3; fi
cd /home/jin/wt_v5_x20 || exit 1
/usr/bin/time -v $PY $D/scripts/x20_static.py > $D/logs/67_v5_static.log 2> $D/logs/67_v5_static.time
echo "exit $?"; grep -E "Maximum resident|Elapsed" $D/logs/67_v5_static.time; tail -c 6000 $D/logs/67_v5_static.log
