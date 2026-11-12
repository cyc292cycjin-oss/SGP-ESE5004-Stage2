#!/bin/bash
# X20 C-2（决策 252）：v5_wind_gwa.py --quantiles -> research_inputs/renewable_v5/WIND_GWA_CELL_QUANTILES_V5.nc / .csv / _LOG.json（格点均值系数重算并与已提交文件逐值比较）。
# 内存门槛：可用 >= 4 GiB 且预计峰值 3 GiB <= 可用 / 2（B 段同脚本 1.69 GB + 直方图 0.31 GB）。
set -u
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
GWA=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x03_renew_20261111/downloads/gwa; LOG=$D/logs/83_gwa_quantiles.log
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj TMPDIR=$D/tmp
cd $R || exit 1
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); PEAK=3221225472
{
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK"; exit 3; fi
echo "MEM_OK available=$AV peak_est=$PEAK"
sha256sum research_inputs/renewable_v5/WIND_GWA_CELL_FACTOR_V5.nc research_inputs/renewable_v5/WIND_GWA_CELL_FACTOR_V5.csv research_inputs/renewable_v5/WIND_GWA_FARM_POINT_FACTOR_V5.csv > $D/cache/gwa_before.sha
/usr/bin/time -v $PY scripts_project/v5_wind_gwa.py --gwa-dir $GWA --quantiles > $D/cache/v5_wind_gwa_q_run.log 2> $D/cache/v5_wind_gwa_q_time.log; echo "exit $?"
grep -E "Maximum resident|Elapsed" $D/cache/v5_wind_gwa_q_time.log; grep -iE "Traceback|Error" $D/cache/v5_wind_gwa_q_time.log | tail -3
tail -1 $D/cache/v5_wind_gwa_q_run.log | cut -c1-1500
echo "== existing outputs unchanged:"; sha256sum -c $D/cache/gwa_before.sha
git status --short research_inputs/renewable_v5
} > $LOG 2>&1
cat $LOG
