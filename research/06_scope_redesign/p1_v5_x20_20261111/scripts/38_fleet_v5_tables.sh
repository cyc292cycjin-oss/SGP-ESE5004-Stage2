#!/bin/bash
# X20 ②5：s4a_2_fleet_data.py（1）严格 / 30 a 复现核对：写 D 盘 cache，与已提交的 v4 表逐字节比较；（2）inclusive / 40 a 写 FLEET_ADDITIONS_2050_V5.csv 等。
# 网络 = 电力底座（17 MB；按 S4A 报告的 748 个身份口径：745 个底座身份 + S1 地热存活记录）。内存门槛：可用 >= 4 GiB 且预计峰值 <= 可用 / 2。
set -u
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; C=$D/cache/fleet_repro; LOG=$D/logs/38_fleet_v5_tables.log
EB=$R/results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc
cd $R || exit 1
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); PEAK=2147483648
{
echo "network $EB sha256 $(sha256sum $EB | cut -c1-64) bytes $(stat -c %s $EB)"
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK"; exit 3; fi
echo "MEM_OK available=$AV peak_est=$PEAK"
rm -rf $C; mkdir -p $C
echo "== (1) strict / 30 a reproduction into $C"
/usr/bin/time -v $PY scripts_project/s4a_2_fleet_data.py --network $EB --out-dir $C > $C/run.log 2> $C/time.log; echo "exit $?"
grep -E "Maximum resident|Elapsed" $C/time.log
for f in $C/*.csv $C/*.json; do b=$(basename $f)
  if [ "$b" = fleet_s4a.csv ]; then ref=research_inputs/registry_v5/fragments/fleet_s4a.csv; else ref=research_inputs/fleet_v5/$b; fi
  if cmp -s $f $ref; then echo "SAME $b"; else echo "DIFF $b"; fi
done
echo "== (2) inclusive / 40 a -> research_inputs/fleet_v5/*_V5.*"
/usr/bin/time -v $PY scripts_project/s4a_2_fleet_data.py --network $EB --boundary inclusive --geothermal-lifetime 40 --v5-out > $C/run_v5.log 2> $C/time_v5.log; echo "exit $?"
grep -E "Maximum resident|Elapsed" $C/time_v5.log; tail -3 $C/time_v5.log | grep -v "Exit status" | head -2
tail -40 $C/run_v5.log
git status --short research_inputs
} > $LOG 2>&1
cat $LOG
