#!/bin/bash
# X20：v5off 与 W14 的回归比较（4 个网络：F1 / F2 × 2920x3h / 365x24h）。内存门槛：可用 >= 4 GiB 且预计峰值 2.5 GiB <= 可用 / 2。
set -u
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; W=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w14/builds/main
LOG=$D/logs/66_v5off_regression.log
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); PEAK=2684354560
{
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK"; exit 3; fi
echo "MEM_OK available=$AV peak_est=$PEAK"
for f in integrated/integrated_2920_3h no_new_xb/no_new_xb_2920_3h integrated/integrated_365_24h no_new_xb/no_new_xb_365_24h; do
  n=$(echo $f | tr / _); echo "== $f"
  /usr/bin/time -v $PY $D/scripts/66_v5off_regression.py $W/${f}_unsolved.nc $D/builds/v5off/${f}_unsolved.nc $D/evidence/V5OFF_VS_W14_$n.json 2> $D/cache/reg_$n.time | grep -E "data_identical|compared|meta_keys_differing|differing\"" 
  grep -E "Maximum resident" $D/cache/reg_$n.time
done
} > $LOG 2>&1
cat $LOG
