#!/bin/bash
# X20 ①1 第二部分（决策 251）：（1）点位系数校准写出 *_V5（α 越界只记录）；（2）有效倍数核对：对照表 v4 / (a) / (b) 写 evidence，v5 主值 (b) 的核对表写 research_inputs。
# 内存门槛：可用 >= 4 GiB 且预计峰值 <= 可用 / 2（校准 2.07 GB 实测；有效倍数整读 wnd100m + 候选格点 float64，按 3.5 GiB 计）。
set -u
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; LOG=$D/logs/47_calib_v5_and_multiplier.log
EMBER=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4b_20261016/sources_s4b/ember/release_generation_yearly_global.csv
RV=research_inputs/renewable_v5
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj TMPDIR=$D/tmp
cd $R || exit 1
gate() { AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); if [ "$AV" -lt 4294967296 ] || [ "$1" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$1"; exit 3; fi; echo "MEM_OK available=$AV peak_est=$1"; }
{
echo "== (1) point-factor calibration -> $RV/*_V5"
gate 3221225472
/usr/bin/time -v $PY scripts_project/s4b_3_wind_calibration.py --ember $EMBER --output $RV --point-factor $RV/WIND_GWA_FARM_POINT_FACTOR_V5.csv > $D/cache/calib_v5_run.log 2> $D/cache/calib_v5_time.log; echo "exit $?"
grep -E "Maximum resident|Elapsed" $D/cache/calib_v5_time.log
$PY -c "import pandas as pd; t=pd.read_csv('$RV/WIND_CALIBRATION_ALPHA_V5.csv'); print(t[['country','calibrated_individually','alpha_main','alpha_grade','alpha_range_low','alpha_range_high','alpha_outside_v4_bound']].to_string(index=False))"
echo "== (2a) comparison v4 / (a) / (b) -> evidence"
gate 3758096384
/usr/bin/time -v $PY scripts_project/v5_wind_effective_multiplier.py --set b=$RV/WIND_CALIBRATION_ALPHA_V5.csv:cell --set a=$D/cache/calib_v5_diag/cell/WIND_CALIBRATION_ALPHA_V5.csv:cell \
   --set v4=$RV/WIND_CALIBRATION_ALPHA.csv --output $D/evidence/WIND_EFFECTIVE_MULTIPLIER_V4_A_B.csv > $D/cache/effmult_cmp.log 2> $D/cache/effmult_cmp_time.log; echo "exit $?"
grep -E "Maximum resident|Elapsed" $D/cache/effmult_cmp_time.log; cat $D/cache/effmult_cmp.log
echo "== (2b) v5 main (b) check -> $RV/WIND_EFFECTIVE_MULTIPLIER_V5.csv"
gate 3758096384
$PY scripts_project/v5_wind_effective_multiplier.py --set b=$RV/WIND_CALIBRATION_ALPHA_V5.csv:cell --output $RV/WIND_EFFECTIVE_MULTIPLIER_V5.csv --json $RV/WIND_EFFECTIVE_MULTIPLIER_V5.json > $D/cache/effmult_b.log 2>&1; echo "exit $?"
tail -2 $D/cache/effmult_b.log
git status --short $RV
} > $LOG 2>&1
cat $LOG
