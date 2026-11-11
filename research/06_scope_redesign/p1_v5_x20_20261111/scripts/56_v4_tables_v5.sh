#!/bin/bash
# X20 ②4 + ①7：v4 表链。（1）v4 主集复现（重写 out_ras，git 须无差异）；（2）v5 主集表级键 -> out_ras_v5。工作目录 D 盘 v4work。
# 内存门槛：可用 >= 4 GiB 且预计峰值 2 GiB <= 可用 / 2。
set -u
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; LOG=$D/logs/56_v4_tables_v5.log
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj TMPDIR=$D/tmp
cd $R || exit 1
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); PEAK=2147483648
{
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK"; exit 3; fi
echo "MEM_OK available=$AV peak_est=$PEAK; start $(date '+%T')"
rm -rf $D/v4work; mkdir -p $D/v4work/repro $D/v4work/v5
echo "== (1) v4 main set reproduction (out_ras)"
/usr/bin/time -v $PY scripts_project/v4_industry.py --work $D/v4work/repro > $D/cache/v4ind_repro.log 2> $D/cache/v4ind_repro.time; echo "exit $?"
grep -E "Maximum resident|Elapsed" $D/cache/v4ind_repro.time; tail -3 $D/cache/v4ind_repro.log | cut -c1-300
echo "git status research_inputs after the reproduction (out_ras must be unchanged):"; git status --short research_inputs | grep -v "^??"; echo "(end)"
echo "== (2) v5 main table keys -> out_ras_v5"
/usr/bin/time -v $PY scripts_project/v4_industry.py --work $D/v4work/v5 --set v5_neu_gas_growth=product --set v5_biomass_residue_fix=corrected > $D/cache/v4ind_v5.log 2> $D/cache/v4ind_v5.time; echo "exit $?"
grep -E "Maximum resident|Elapsed" $D/cache/v4ind_v5.time; tail -3 $D/cache/v4ind_v5.log | cut -c1-300
ls research_inputs/industry_v4/out_ras_v5/
git status --short research_inputs | head; echo "end $(date '+%T')"
} > $LOG 2>&1
cat $LOG
