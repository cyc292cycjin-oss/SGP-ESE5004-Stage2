#!/bin/bash
# W14 section 4: alarm lines from the v3.1 2920x3h HPC solutions (no solver). Memory rule of the instruction: no Gurobi process on this machine, >= 8 GiB
# available before reading the v3.1 solved networks; the two runs are read one after the other (scripts/w14_bounds_pre.py).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w14_20261109; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[g]urobi_cl')" = 0 ] || { echo "REFUSED: a Gurobi process is running"; exit 2; }
avail=$(awk '/MemAvailable/ {printf "%d", $2/1048576}' /proc/meminfo); echo "MemAvailable ${avail} GiB"
[ "$avail" -ge 8 ] || { echo "REFUSED: available memory ${avail} GiB < 8 GiB"; exit 2; }
cd $W && env -u GRB_LICENSE_FILE /usr/bin/time -v $PY scripts/w14_bounds_pre.py > logs/bounds_pre.txt 2> logs/bounds_pre.err; echo "BOUNDS_EXIT:$?"
grep -v -iE 'warn|INFO:|PROJ' logs/bounds_pre.txt | cut -c1-3000; grep -E 'Maximum resident|Elapsed|Error|Traceback' logs/bounds_pre.err; tail -5 logs/bounds_pre.err
