#!/bin/bash
# V3 supplement 01 step 1: the flat control networks (decision 165 switch, same stock as X1): integrated built with --override s2.demand.ev_structure=flat at a clean commit, no_new_xb derived from it,
# 56-snapshot LP sizes, comparison with the E2 networks. No solver call, no licence. Status in results_project/v3/builds_flat/BUILD_STATUS.txt
set -u
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
OUT=$MAIN/results_project/v3/builds_flat; ST=$OUT/BUILD_STATUS.txt
cd $W || exit 1
DIRTY=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)
[ "$DIRTY" = 0 ] || { echo "REFUSED: tracked changes not committed ($DIRTY)"; exit 2; }
[ ! -e "$OUT" ] || { echo "REFUSED: $OUT exists"; exit 2; }
mkdir -p $OUT/integrated $OUT/no_new_xb
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD)" > $ST
/usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/integrated --override s2.demand.ev_structure=flat > $OUT/integrated_build.log 2> $OUT/integrated_build.err
echo "BUILD_integrated_flat:$?:$(tail -1 $OUT/integrated_build.log | cut -c1-110)" >> $ST
for r in 2920_3h 365_24h; do
  $PY scripts_project/m08a_variants.py --repo . --base $OUT/integrated/integrated_${r}_unsolved.nc --out $OUT/no_new_xb --set cross_border.stock_mode=no_new_xb > $OUT/no_new_xb_$r.log 2>&1
  echo "VARIANT_$r:$?" >> $ST
done
( cd $OUT && sha256sum */*_unsolved.nc ) >> $ST
ls -l $OUT/*/*_unsolved.nc | awk '{print $5, $9}' >> $ST
for s in integrated no_new_xb; do
  L=$OUT/lp_${s}_t56; mkdir -p $L
  env GRB_LICENSE_FILE=/nonexistent /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/$s/${s}_2920_3h_unsolved.nc --scenario $s --output $L --solver gurobi --truncate 56 --label SMOKE_TEST_ONLY --authorization "V3 supplement 01 build check, no solver call" --stop-before-solve > $L/out.log 2> $L/err.log
  echo "LP_${s}_t56:$?:$(tail -1 $L/out.log | cut -c1-170)" >> $ST
  rm -f $L/*.lp
done
cd $W/scripts_project && $PY /home/jin/v3/chk_flat.py >> $ST 2>&1
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
cut -c1-230 $ST
