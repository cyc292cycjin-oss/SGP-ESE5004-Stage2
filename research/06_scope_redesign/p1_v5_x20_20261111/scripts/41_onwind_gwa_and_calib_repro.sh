#!/bin/bash
# X20 ①1 第一段：（1）worktree 只读符号链接 cutouts、results_project/s4a（指向主检出）；（2）正式运行 v5_wind_gwa.py -> research_inputs/renewable_v5，与 D 盘试跑结果比较；
# （3）未改动的 s4b_3_wind_calibration.py 复现 v4 alpha 表（输出 D 盘 cache/calib_repro），与已提交的表比较。
# 内存门槛：可用 >= 4 GiB 且预计峰值 <= 可用 / 2（GWA 试跑 1.69 GB；校准整读 wnd100m 约 2-3 GB，按 3 GiB 计）。
set -u
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; LOG=$D/logs/41_onwind_gwa_and_calib_repro.log
GWA=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x03_renew_20261111/downloads/gwa
EMBER=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4b_20261016/sources_s4b/ember/release_generation_yearly_global.csv
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj TMPDIR=$D/tmp
mkdir -p $D/tmp
cd $R || exit 1
gate() { AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); if [ "$AV" -lt 4294967296 ] || [ "$1" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$1"; exit 3; fi; echo "MEM_OK available=$AV peak_est=$1"; }
{
[ -e cutouts ] || ln -s $MAIN/cutouts cutouts
[ -e results_project/s4a ] || ln -s $MAIN/results_project/s4a results_project/s4a
ls -la cutouts results_project/s4a | cut -c1-200
echo "cutout $(stat -c %s cutouts/asean_zenodo_20325289/cutout-2013-era5.nc) B"
echo "ember $EMBER $(stat -c %s $EMBER) B sha256 $(sha256sum $EMBER | cut -c1-64)"
echo "== (2) v5_wind_gwa.py"
gate 1932735283
cp $D/x20_src/scripts_project/v5_wind_gwa.py scripts_project/v5_wind_gwa.py; sed -i 's/\r$//' scripts_project/v5_wind_gwa.py; chmod 644 scripts_project/v5_wind_gwa.py
/usr/bin/time -v $PY scripts_project/v5_wind_gwa.py --gwa-dir $GWA > $D/cache/v5_wind_gwa_run.log 2> $D/cache/v5_wind_gwa_time.log; echo "exit $?"
grep -E "Maximum resident|Elapsed" $D/cache/v5_wind_gwa_time.log; tail -1 $D/cache/v5_wind_gwa_run.log | cut -c1-600
for f in WIND_GWA_CELL_FACTOR_V5.nc WIND_GWA_CELL_FACTOR_V5.csv WIND_GWA_FARM_POINT_FACTOR_V5.csv; do
  if cmp -s research_inputs/renewable_v5/$f $D/cache/wind_gwa/$f; then echo "SAME as trial: $f"; else echo "DIFF from trial: $f"; fi; done
echo "== (3) s4b_3_wind_calibration.py (v4 code) reproduction"
gate 3221225472
rm -rf $D/cache/calib_repro; mkdir -p $D/cache/calib_repro
/usr/bin/time -v $PY scripts_project/s4b_3_wind_calibration.py --ember $EMBER --output $D/cache/calib_repro > $D/cache/calib_repro/run.log 2> $D/cache/calib_repro/time.log; echo "exit $?"
grep -E "Maximum resident|Elapsed" $D/cache/calib_repro/time.log
for f in WIND_CALIBRATION_ALPHA.csv WIND_OBSERVED_CF_EMBER_2019_2025.csv WIND_OBSERVED_CF_SUMMARY.csv WIND_FARMS_MODEL_CF_2013.csv WIND_CALIBRATION_S4B3.json; do
  if cmp -s research_inputs/renewable_v5/$f $D/cache/calib_repro/$f; then echo "SAME: $f"; else echo "DIFF: $f"; fi; done
$PY - <<'P'
import pandas as pd, numpy as np
a = pd.read_csv("research_inputs/renewable_v5/WIND_CALIBRATION_ALPHA.csv").set_index("country")
b = pd.read_csv("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/cache/calib_repro/WIND_CALIBRATION_ALPHA.csv").set_index("country")
num = [c for c in a.columns if a[c].dtype.kind == "f"]
print("alpha_main committed / repro / max abs diff over numeric columns:")
print(pd.DataFrame(dict(committed=a.alpha_main, repro=b.alpha_main)).to_string())
print("max abs diff", float(np.nanmax(np.abs(a[num].values - b[num].values))))
P
git status --short | head
} > $LOG 2>&1
cat $LOG
