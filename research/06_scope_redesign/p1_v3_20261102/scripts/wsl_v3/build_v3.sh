#!/bin/bash
# V3 phase 3 item 3: builds at a clean commit, static checks, LP sizes (no solver call, no licence). Status in results_project/v3/builds/BUILD_STATUS.txt
set -u
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=$W/research/06_scope_redesign/p1_v3_20261102
OUT=$MAIN/results_project/v3/builds; ST=$OUT/BUILD_STATUS.txt
cd $W || exit 1
DIRTY=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)
[ "$DIRTY" = 0 ] || { echo "REFUSED: tracked changes not committed ($DIRTY)"; exit 2; }
rm -rf $OUT; mkdir -p $OUT
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD)" > $ST
for t in integrated disconnected; do
  mkdir -p $OUT/$t
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $t --output $OUT/$t > $OUT/${t}_build.log 2> $OUT/${t}_build.err
  echo "BUILD_$t:$?:$(tail -1 $OUT/${t}_build.log | cut -c1-110):$(grep -h 'Maximum resident' $OUT/${t}_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/${t}_build.err | tr -s ' ' | cut -c30-)" >> $ST
done
mkdir -p $OUT/no_new_xb
for r in 2920_3h 365_24h; do
  $PY scripts_project/m08a_variants.py --repo . --base $OUT/integrated/integrated_${r}_unsolved.nc --out $OUT/no_new_xb --set cross_border.stock_mode=no_new_xb > $OUT/no_new_xb_$r.log 2>&1
  echo "VARIANT_$r:$?:$(grep -c sha256 $OUT/no_new_xb_$r.log)" >> $ST
done
( cd $OUT && sha256sum */*_unsolved.nc ) >> $ST
ls -l $OUT/*/*_unsolved.nc | awk '{print $5, $9}' >> $ST
cd $W/scripts_project
$PY v3_static.py --dir $OUT --v2 $MAIN/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc --out $D > $OUT/static.log 2>&1
echo "STATIC:$?" >> $ST
cd $W
for spec in "integrated 2920_3h 56" "no_new_xb 2920_3h 56" "integrated 365_24h 0" "no_new_xb 365_24h 0"; do
  set -- $spec; s=$1; r=$2; tr=$3; L=$OUT/lp_${s}_${r}_t$tr; mkdir -p $L
  env GRB_LICENSE_FILE=/nonexistent /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/$s/${s}_${r}_unsolved.nc --scenario $s --output $L --solver gurobi --truncate $tr --label V3_BUILD_CHECK --authorization "V3 phase 3 build check, no solver call" --stop-before-solve > $L/out.log 2> $L/err.log
  echo "LP_${s}_${r}_t$tr:$?:$(tail -1 $L/out.log | cut -c1-210):$(grep -h 'Maximum resident' $L/err.log | tr -s ' ')" >> $ST
  rm -f $L/*.lp
done
echo DONE >> $ST
cat $ST | cut -c1-260
