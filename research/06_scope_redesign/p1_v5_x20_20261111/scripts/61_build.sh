#!/bin/bash
# X20 构建（不求解、无许可证）：<set>/integrated = s2_network.py（2920x3h 与 365x24h），<set>/no_new_xb = m08a_variants.py --set cross_border.stock_mode=no_new_xb。
# 用法：61_build.sh <set> <v5main | v5off> [variants: yes | no]；输出 D 盘 builds/<set>（不复用已有目录）。
#   v5main = --override demand.v4.enabled=true --override demand.v5.enabled=true；v5off = --override demand.v4.enabled=true（与 W14 对照）。
# 内存门槛：可用 >= 4 GiB 且预计峰值 1.5 GiB <= 可用 / 2（W14 1.06 GB）。
set -u
SET=${1:?set}; MODE=${2:?mode}; VAR=${3:-yes}
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
OUT=$D/builds/$SET; ST=$OUT/BUILD_STATUS.txt
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj TMPDIR=$D/tmp
cd $R || exit 1
case $MODE in v5main) OV="--override demand.v4.enabled=true --override demand.v5.enabled=true";; v5off) OV="--override demand.v4.enabled=true";; *) echo "mode?"; exit 2;; esac
[ ! -e "$OUT" ] || { echo "REFUSED: $OUT exists"; exit 2; }
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[s]2_network\.py|[g]urobi_cl')" = 0 ] || { echo "REFUSED: another solve or build is running"; exit 2; }
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); PEAK=1610612736
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK"; exit 3; fi
mkdir -p $OUT/integrated
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD) dirty_tracked:$(git status --porcelain --untracked-files=no | wc -l) set:$SET mode:$MODE overrides:$OV MEM_OK available=$AV" >> $ST
/usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/integrated $OV > $OUT/integrated_build.log 2> $OUT/integrated_build.err
echo "BUILD_integrated:$?:$(grep -h 'Maximum resident' $OUT/integrated_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/integrated_build.err | tr -s ' ' | cut -c30-):$(date -u +%H:%M:%S)" >> $ST
if [ "$VAR" = yes ]; then
  for z in 2920_3h 365_24h; do
    /usr/bin/time -v $PY scripts_project/m08a_variants.py --repo . --base $OUT/integrated/integrated_${z}_unsolved.nc --out $OUT/no_new_xb --set cross_border.stock_mode=no_new_xb > $OUT/no_new_xb_$z.log 2> $OUT/no_new_xb_$z.err
    echo "VARIANT_no_new_xb_$z:$?:$(grep -h 'Maximum resident' $OUT/no_new_xb_$z.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/no_new_xb_$z.err | tr -s ' ' | cut -c30-)" >> $ST
  done
fi
( cd $OUT && sha256sum */*_unsolved.nc ) >> $ST 2>/dev/null
ls -l $OUT/*/*_unsolved.nc 2>/dev/null | awk '{print $5, $9}' >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
cat $ST; tail -5 $OUT/integrated_build.err | grep -v -E "^\s+(Command|User|System|Percent|Average|Major|Minor|Volun|Invol|Swaps|File|Socket|Signals|Page|Exit)"
