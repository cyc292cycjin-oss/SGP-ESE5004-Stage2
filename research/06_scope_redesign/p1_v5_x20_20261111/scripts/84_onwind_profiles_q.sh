#!/bin/bash
# X20 C-2 剖面：s4a_profiles.py --variant calibrated_modern calibrated_gwa_v5 calibrated_gwa_v5q --techs onwind --classes N，输出 D 盘 profiles/onwind_q_cN。
# calibrated_modern 与 calibrated_gwa_v5 须与已提交的 profiles_*_cN_3h.nc 的 onwind 逐值相同（复现核对，证明 C-2 未改原路径）。用法：84_onwind_profiles_q.sh <N>
# 内存门槛：可用 >= 4 GiB 且预计峰值 4.5 GiB <= 可用 / 2（B 段同类运行 1.87 GB）。
set -u
N=${1:?classes}
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; O=$D/profiles/onwind_q_c$N; LOG=$D/logs/84_onwind_profiles_q_c$N.log
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj TMPDIR=$D/tmp
cd $R || exit 1
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); PEAK=4831838208
{
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK"; exit 3; fi
echo "MEM_OK available=$AV peak_est=$PEAK"
rm -rf $O; mkdir -p $O
/usr/bin/time -v $PY scripts_project/s4a_profiles.py --variant calibrated_modern calibrated_gwa_v5 calibrated_gwa_v5q --techs onwind --classes $N --output $O > $O/run.log 2> $O/time.log; echo "exit $?"
grep -E "Maximum resident|Elapsed" $O/time.log; grep -iE "Traceback|Error" $O/time.log | tail -3; tail -2 $O/run.log | cut -c1-400
$PY - "$O" "$N" <<'P'
import sys
import numpy as np, xarray as xr
O, N = sys.argv[1], sys.argv[2]
for var in ("calibrated_modern", "calibrated_gwa_v5"):
    ref = xr.open_dataset(f"/home/jin/wt_v5_x20/research_inputs/renewable_v5/profiles_{var}_c{N}_3h.nc")["onwind"]
    new = xr.open_dataarray(f"{O}/profile_onwind_{var}_c{N}_3h.nc").transpose("time", "bus").astype("float32").clip(0, 1).sel(bus=ref.bus.values)
    print(var, "repro: buses", ref.sizes["bus"], "max abs diff", float(np.nanmax(np.abs(new.values - ref.values))), "identical", bool((new.values == ref.values).all()))
q = xr.open_dataarray(f"{O}/profile_onwind_calibrated_gwa_v5q_c{N}_3h.nc").transpose("time", "bus")
print("calibrated_gwa_v5q: buses", q.sizes["bus"], "mean CF", float(q.mean()), "min", float(q.min()), "max", float(q.max()))
P
du -sb $O
} > $LOG 2>&1
cat $LOG
