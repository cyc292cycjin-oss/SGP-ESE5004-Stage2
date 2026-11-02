#!/bin/bash
# V3 phase 3 item 3, second pass on the networks built at 85095e7a (not rebuilt): corrected static check, 56-snapshot LP sizes with the label s2_solve requires for a truncated horizon. No solver call, no licence.
set -u
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=$W/research/06_scope_redesign/p1_v3_20261102
OUT=$MAIN/results_project/v3/builds; ST=$OUT/BUILD_STATUS.txt
cd $W/scripts_project
$PY v3_static.py --dir $OUT --v2 $MAIN/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc --out $D > $OUT/static2.log 2>&1
echo "STATIC2:$?:code $(git rev-parse --short HEAD) + v3_static edit" >> $ST
cd $W
for spec in "integrated 2920_3h 56" "no_new_xb 2920_3h 56"; do
  set -- $spec; s=$1; r=$2; tr=$3; L=$OUT/lp_${s}_${r}_t$tr; rm -rf $L; mkdir -p $L
  env GRB_LICENSE_FILE=/nonexistent /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/$s/${s}_${r}_unsolved.nc --scenario $s --output $L --solver gurobi --truncate $tr --label SMOKE_TEST_ONLY --authorization "V3 phase 3 build check, no solver call" --stop-before-solve > $L/out.log 2> $L/err.log
  echo "LP2_${s}_${r}_t$tr:$?:$(tail -1 $L/out.log | cut -c1-210):$(grep -h 'Maximum resident' $L/err.log | tr -s ' ')" >> $ST
  rm -f $L/*.lp
done
echo DONE2 >> $ST
tail -8 $ST | cut -c1-260
