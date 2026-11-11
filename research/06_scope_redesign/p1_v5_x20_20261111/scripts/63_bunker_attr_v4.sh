#!/bin/bash
# X20 ③5：v5_bunker_attribution.py 在 v4 W14 2920x3h 已解网络 F1 / F2 上（X10 备忘录：F1 合成端碳 130.96 Mt，燃料舱约 117-121 Mt）。内存门槛：可用 >= 4 GiB 且预计峰值 2 GiB <= 可用 / 2。
set -u
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; V=$D/cache/v4solved/export; LOG=$D/logs/63_bunker_attr_v4.log
export PYTHONHASHSEED=0
cd $R/scripts_project || exit 1
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); PEAK=2147483648
{
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK"; exit 3; fi
echo "MEM_OK available=$AV peak_est=$PEAK"
for r in F1:integrated F2:no_new_xb; do k=${r%%:*}; s=${r##*:}
  /usr/bin/time -v $PY v5_bunker_attribution.py --network $V/$k/${s}_BATCH4_2920X3H_solved.nc --output $D/evidence --name BUNKER_CARBON_ATTRIBUTION_V4_W14_$k 2> $D/cache/battr_$k.time; echo "$k exit $?"
  grep -E "Maximum resident|Elapsed" $D/cache/battr_$k.time; grep -v -E "^\s" $D/cache/battr_$k.time | tail -3
done
} > $LOG 2>&1
cat $LOG
