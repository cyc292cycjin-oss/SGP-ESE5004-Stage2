#!/bin/bash
# X20 ①1 第二段：改后的 s4b_3_wind_calibration.py（a）v4 模式再复现一次（D 盘 cache/calib_repro2，须与已提交表逐字节相同）；（b）点位系数模式 -> research_inputs/renewable_v5/*_V5。
set -u
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; LOG=$D/logs/42_calib_v5.log
EMBER=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4b_20261016/sources_s4b/ember/release_generation_yearly_global.csv
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj TMPDIR=$D/tmp
cd $R || exit 1
gate() { AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); if [ "$AV" -lt 4294967296 ] || [ "$1" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$1"; exit 3; fi; echo "MEM_OK available=$AV peak_est=$1"; }
{
echo "== (a) v4 mode reproduction after the edit"
gate 3221225472
rm -rf $D/cache/calib_repro2; mkdir -p $D/cache/calib_repro2
$PY scripts_project/s4b_3_wind_calibration.py --ember $EMBER --output $D/cache/calib_repro2 > $D/cache/calib_repro2/run.log 2>&1; echo "exit $?"
for f in WIND_CALIBRATION_ALPHA.csv WIND_OBSERVED_CF_EMBER_2019_2025.csv WIND_OBSERVED_CF_SUMMARY.csv WIND_FARMS_MODEL_CF_2013.csv WIND_CALIBRATION_S4B3.json; do
  if cmp -s research_inputs/renewable_v5/$f $D/cache/calib_repro2/$f; then echo "SAME: $f"; else echo "DIFF: $f"; fi; done
echo "== (b) point-factor mode (Q1 (b))"
gate 3221225472
/usr/bin/time -v $PY scripts_project/s4b_3_wind_calibration.py --ember $EMBER --output research_inputs/renewable_v5 --point-factor research_inputs/renewable_v5/WIND_GWA_FARM_POINT_FACTOR_V5.csv > $D/cache/calib_v5_run.log 2> $D/cache/calib_v5_time.log; echo "exit $?"
grep -E "Maximum resident|Elapsed" $D/cache/calib_v5_time.log; tail -3 $D/cache/calib_v5_run.log
$PY - <<'P'
import pandas as pd
a = pd.read_csv("research_inputs/renewable_v5/WIND_CALIBRATION_ALPHA.csv").set_index("country")
b = pd.read_csv("research_inputs/renewable_v5/WIND_CALIBRATION_ALPHA_V5.csv").set_index("country")
t = pd.DataFrame(dict(farms=b.farms, cf_obs=b.cf_obs, cal=b.calibrated_individually, alpha_v4=a.alpha_main, alpha_v5=b.alpha_main, grade_v5=b.alpha_grade.str[:1],
                      lo=b.alpha_range_low, hi=b.alpha_range_high, fp_w=b.factor_point_capacity_weighted, cf1_v4=a.cf_model_alpha1_nrel_atb2020_4mw, cf1_v5=b.cf_model_alpha1_nrel_atb2020_4mw,
                      cf_dea_v4=a.cf_farms_dea2050_alpha_main, cf_dea_v5=b.cf_farms_dea2050_alpha_main))
pd.set_option("display.width", 250); print(t.round(4).to_string())
fm = pd.read_csv("research_inputs/renewable_v5/WIND_FARMS_MODEL_CF_2013_V5.csv")
for c in ("PH", "TH", "VN"):
    d = fm[fm.iso == c]; print(c, "calibrated farm CF (NREL 4 MW, capacity-weighted)", round(float((d.cf_calibrated_nrel4mw * d["Capacity (MW)"]).sum() / d["Capacity (MW)"].sum()), 8), "obs", round(float(b.at[c, "cf_obs"]), 8))
P
git status --short research_inputs/renewable_v5
} > $LOG 2>&1
cat $LOG
