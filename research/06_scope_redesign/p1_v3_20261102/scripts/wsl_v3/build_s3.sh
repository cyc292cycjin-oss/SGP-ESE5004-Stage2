#!/bin/bash
# V3 supplement 03 (review item 2.2, one-way plant lines): builds at a clean commit, no solver call, no licence. integrated + no_new_xb (2920x3h, 365x24h), v3 disconnected (365x24h, decision 174), two bridge networks
# (365x24h: decisions 160-162 = flat + empty industry v3 tables; 160-164 = flat), static checks, LP sizes (56 snapshots and full 365x24h). Status in results_project/v3/builds_oneway/BUILD_STATUS.txt
set -u
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=$W/research/06_scope_redesign/p1_v3_20261102; OUT=$MAIN/results_project/v3/builds_oneway; ST=$OUT/BUILD_STATUS.txt
cd $W || exit 1
DIRTY=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)
[ "$DIRTY" = 0 ] || { echo "REFUSED: tracked changes not committed ($DIRTY)"; exit 2; }
[ ! -e "$OUT" ] || { echo "REFUSED: $OUT exists"; exit 2; }
mkdir -p $OUT/integrated $OUT/no_new_xb $OUT/disconnected $OUT/bridge_160_162 $OUT/bridge_160_164
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD)" > $ST
build() {   # folder, scenario, overrides...
  f=$1; s=$2; shift 2
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $s --output $OUT/$f "$@" > $OUT/${f}_build.log 2> $OUT/${f}_build.err
  echo "BUILD_$f:$?:$(grep -h 'Maximum resident' $OUT/${f}_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/${f}_build.err | tr -s ' ' | cut -c30-):$(date -u +%H:%M:%S)" >> $ST
}
build integrated integrated
for r in 2920_3h 365_24h; do
  $PY scripts_project/m08a_variants.py --repo . --base $OUT/integrated/integrated_${r}_unsolved.nc --out $OUT/no_new_xb --set cross_border.stock_mode=no_new_xb > $OUT/no_new_xb_$r.log 2>&1
  echo "VARIANT_$r:$?" >> $ST
done
build disconnected disconnected
build bridge_160_164 integrated --override s2.demand.ev_structure=flat
build bridge_160_162 integrated --override s2.demand.ev_structure=flat --override 's2.industry.v3={}'
rm -f $OUT/disconnected/disconnected_2920_3h_unsolved.nc $OUT/bridge_160_164/integrated_2920_3h_unsolved.nc $OUT/bridge_160_162/integrated_2920_3h_unsolved.nc   # 365x24h only (decision 174; bridge runs are screening runs)
( cd $OUT && sha256sum */*_unsolved.nc ) >> $ST
ls -l $OUT/*/*_unsolved.nc | awk '{print $5, $9}' >> $ST
( cd $W/scripts_project && $PY v3_static.py --dir $OUT --v2 $MAIN/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc --out $D > $OUT/static.log 2>&1; echo "STATIC:$?" >> $ST )
( cd $W/scripts_project && $PY /home/jin/v3/chk_bridge.py $OUT $D/evidence > $OUT/bridge.log 2>&1; echo "BRIDGE_CHECK:$?" >> $ST )
for spec in "integrated integrated 365_24h 0" "no_new_xb no_new_xb 365_24h 0" "disconnected disconnected 365_24h 0" "bridge_160_164 integrated 365_24h 0" "bridge_160_162 integrated 365_24h 0"; do
  set -- $spec; f=$1; s=$2; r=$3; tr=$4; L=$OUT/lp_${f}_${r}_t$tr; mkdir -p $L
  env GRB_LICENSE_FILE=/nonexistent /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/$f/${s}_${r}_unsolved.nc --scenario $s --output $L --solver gurobi --truncate $tr --label V3_BUILD_CHECK --authorization "V3 supplement 02 build check, no solver call" --stop-before-solve > $L/out.log 2> $L/err.log
  echo "LP_${f}_${r}_t$tr:$?:$(tail -1 $L/out.log | cut -c1-210):$(grep -h 'Maximum resident' $L/err.log | tr -s ' ')" >> $ST
  rm -f $L/*.lp
done
for s in integrated no_new_xb; do
  L=$OUT/lp_${s}_2920_3h_t56; mkdir -p $L
  env GRB_LICENSE_FILE=/nonexistent /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/$s/${s}_2920_3h_unsolved.nc --scenario $s --output $L --solver gurobi --truncate 56 --label SMOKE_TEST_ONLY --authorization "V3 supplement 03 build check, no solver call" --stop-before-solve > $L/out.log 2> $L/err.log
  echo "LP_${s}_t56:$?:$(tail -1 $L/out.log | cut -c1-120)" >> $ST
  rm -f $L/*.lp
done
$PY /home/jin/v3/chk_disc.py $MAIN/results_project/v3/builds_x1b/disconnected/disconnected_365_24h_unsolved.nc $OUT/disconnected/disconnected_365_24h_unsolved.nc >> $ST 2>&1
du -sh $OUT >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
cut -c1-260 $ST
