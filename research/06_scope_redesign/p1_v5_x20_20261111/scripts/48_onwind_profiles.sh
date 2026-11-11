#!/bin/bash
# X20 ①1 剖面：s4a_profiles.py --variant calibrated_modern calibrated_gwa_v5 --techs onwind --classes N，输出 D 盘 profiles/onwind_cN。
# calibrated_modern 与已提交的 profiles_calibrated_modern_cN_3h.nc 的 onwind 逐值比较（复现核对）。用法：48_onwind_profiles.sh <N>
# 内存门槛：可用 >= 4 GiB 且预计峰值 <= 可用 / 2（规格 §4 估 3-5 GB；先跑 c1 实测，按 4.5 GiB 计）。
set -u
N=${1:?classes}
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; O=$D/profiles/onwind_c$N; LOG=$D/logs/48_onwind_profiles_c$N.log
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj TMPDIR=$D/tmp
cd $R || exit 1
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); PEAK=${PEAK:-4831838208}
{
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK"; exit 3; fi
echo "MEM_OK available=$AV peak_est=$PEAK"
rm -rf $O; mkdir -p $O
/usr/bin/time -v $PY scripts_project/s4a_profiles.py --variant calibrated_modern calibrated_gwa_v5 --techs onwind --classes $N --output $O > $O/run.log 2> $O/time.log; echo "exit $?"
grep -E "Maximum resident|Elapsed" $O/time.log; tail -2 $O/run.log | cut -c1-300
$PY - "$O" "$N" <<'P'
import sys
import numpy as np, xarray as xr
O, N = sys.argv[1], sys.argv[2]
ref = xr.open_dataset(f"/home/jin/wt_v5_x20/research_inputs/renewable_v5/profiles_calibrated_modern_c{N}_3h.nc")["onwind"]
new = xr.open_dataarray(f"{O}/profile_onwind_calibrated_modern_c{N}_3h.nc").transpose("time", "bus").astype("float32").clip(0, 1)
new = new.sel(bus=ref.bus.values)
d = np.abs(new.values - ref.values)
print("calibrated_modern repro: buses", ref.sizes["bus"], "max abs diff", float(np.nanmax(d)), "identical", bool((new.values == ref.values).all()))
v5 = xr.open_dataarray(f"{O}/profile_onwind_calibrated_gwa_v5_c{N}_3h.nc").transpose("time", "bus")
print("calibrated_gwa_v5: buses", v5.sizes["bus"], "mean CF v4", float(ref.mean()), "v5", float(v5.mean()))
P
du -sb $O
} > $LOG 2>&1
cat $LOG
