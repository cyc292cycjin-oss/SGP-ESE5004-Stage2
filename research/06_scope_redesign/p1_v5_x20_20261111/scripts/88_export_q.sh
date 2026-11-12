#!/bin/bash
# X20 C-2（决策 252、253）：s4b_3_export.py --variant calibrated_gwa_v5q（c1、c3）-> research_inputs/renewable_v5；海上与光伏须与 calibrated_modern 逐值相同（脚本内断言）。
set -u
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; LOG=$D/logs/88_export_q.log
export PYTHONHASHSEED=0
cd $R || exit 1
{
for N in 1 3; do $PY scripts_project/s4b_3_export.py --classes $N --variant calibrated_gwa_v5q --onwind-source $D/profiles/onwind_q_c$N; echo "c$N exit $?"; done
ls -la research_inputs/renewable_v5/ | grep -E "gwa_v5q|MANIFEST|QUANTILES"
git status --short research_inputs/renewable_v5
} > $LOG 2>&1
cat $LOG
