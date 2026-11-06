#!/bin/bash
# W08: write the v4 network tables (out_ras = v4 main, out_iid = IId sensitivity) and check them against I2.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106; R=/home/jin/wt_v4_w08; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
cd $R || exit 1
for m in ras iid; do
  $PY scripts_project/v4_industry.py --anchor-mode $m --work /home/jin/v4w08/work_out_$m > /home/jin/v4w08/out_$m.log 2>&1 || { tail -30 /home/jin/v4w08/out_$m.log; exit 1; }
  tail -12 /home/jin/v4w08/out_$m.log
done
cd $W && $PY scripts/w08_check_outputs.py
