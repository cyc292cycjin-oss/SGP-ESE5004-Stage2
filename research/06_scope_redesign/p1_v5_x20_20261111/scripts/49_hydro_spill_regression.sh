#!/bin/bash
# X20 ①5：v5_hydro_spill.py 在 v4 W14 2920x3h 已解网络上的回归（须复现 X03：F1 527.0 / 519.9 / 7.1，F2 528.9 / 521.5 / 7.4 TWh）。
# 内存门槛：可用 >= 4 GiB 且预计峰值 1 GiB <= 可用 / 2（xarray 只读 storage_units 静态列、母线国别、权重与 inflow / spill）。
set -u
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; V=$D/cache/v4solved/export; LOG=$D/logs/49_hydro_spill_regression.log
export PYTHONHASHSEED=0
cd $R/scripts_project || exit 1
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); PEAK=1073741824
{
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK"; exit 3; fi
echo "MEM_OK available=$AV peak_est=$PEAK"
for r in F1:integrated F2:no_new_xb; do k=${r%%:*}; s=${r##*:}
  /usr/bin/time -v $PY v5_hydro_spill.py --network $V/$k/${s}_BATCH4_2920X3H_solved.nc --output $D/evidence/HYDRO_SPILL_V4_W14_$k.json 2> $D/cache/spill_$k.time; echo "$k exit $?"
  grep -E "Maximum resident|Elapsed" $D/cache/spill_$k.time
done
} > $LOG 2>&1
cat $LOG
