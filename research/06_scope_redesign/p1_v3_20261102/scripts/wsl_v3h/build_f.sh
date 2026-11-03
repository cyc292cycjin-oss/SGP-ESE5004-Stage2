#!/bin/bash
# V3 HPC package step 2 (instruction V14 section 2): build the four 2920x3h networks at the clean commit (no solver call, no licence).
#   sa/      F1 integrated, F2 no_new_xb (S-A shipping, decision 187)
#   sa_ev05/ F3 integrated, F4 no_new_xb (S-A + EV fleet proxy x 0.5, decision 186: --override s2.demand.ev_fleet_scale=0.5)
# The 365x24h files of each root are built too (v3_static.py checks both resolutions); they are never packaged.
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj
W=/home/jin/wt_v3_hpc; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=$W/research/06_scope_redesign/p1_v3_20261102
OUT=$MAIN/results_project/v3hpc/builds; ST=$OUT/BUILD_STATUS.txt
cd $W || exit 1
DIRTY=$(git status --porcelain --untracked-files=no | wc -l)
[ "$DIRTY" = 0 ] || { echo "REFUSED: tracked changes not committed ($DIRTY)"; exit 2; }
[ ! -e "$OUT" ] || { echo "REFUSED: $OUT exists"; exit 2; }
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[p]ytest|[s]2_network\.py')" = 0 ] || { echo "REFUSED: another solve, build or pytest is running"; exit 2; }
mkdir -p $OUT
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD)" > $ST
build() {   # root, overrides...
  r=$1; shift; mkdir -p $OUT/$r/integrated $OUT/$r/no_new_xb $OUT/$r/static
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/$r/integrated "$@" > $OUT/$r/integrated_build.log 2> $OUT/$r/integrated_build.err
  echo "BUILD_$r:$?:$(grep -h 'Maximum resident' $OUT/$r/integrated_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/$r/integrated_build.err | tr -s ' ' | cut -c30-):$(date -u +%H:%M:%S)" >> $ST
  for z in 2920_3h 365_24h; do
    $PY scripts_project/m08a_variants.py --repo . --base $OUT/$r/integrated/integrated_${z}_unsolved.nc --out $OUT/$r/no_new_xb --set cross_border.stock_mode=no_new_xb > $OUT/$r/no_new_xb_$z.log 2>&1
    echo "VARIANT_${r}_$z:$?" >> $ST
  done
  cp $D/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v3.csv $OUT/$r/static/   # v3_static.py reads it from its --out folder (supplement 07 note)
  ( cd $W/scripts_project && $PY v3_static.py --dir $OUT/$r --v2 $MAIN/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc --out $OUT/$r/static > $OUT/$r/static.log 2>&1; echo "STATIC_$r:$?" >> $ST )
}
build sa
build sa_ev05 --override s2.demand.ev_fleet_scale=0.5
( cd $OUT && sha256sum */*/*_unsolved.nc ) >> $ST
ls -l $OUT/*/*/*_unsolved.nc | awk '{print $5, $9}' >> $ST
du -sh $OUT >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
