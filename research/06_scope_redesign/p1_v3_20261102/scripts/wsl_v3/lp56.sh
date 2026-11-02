#!/bin/bash
# V3 supplement 02: 56-snapshot LP sizes (label of a truncated run), no solver, no licence
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; OUT=$MAIN/results_project/v3/builds_x1b; ST=$OUT/BUILD_STATUS.txt
cd $W
tail -3 $OUT/lp_integrated_2920_3h_t56/err.log | cut -c1-200
for s in integrated no_new_xb; do
  L=$OUT/lp_${s}_2920_3h_t56b; mkdir -p $L
  env GRB_LICENSE_FILE=/nonexistent /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/$s/${s}_2920_3h_unsolved.nc --scenario $s --output $L --solver gurobi --truncate 56 --label SMOKE_TEST_ONLY --authorization "V3 supplement 02 build check, no solver call" --stop-before-solve > $L/out.log 2> $L/err.log
  echo "LP_${s}_t56b:$?:$(tail -1 $L/out.log | cut -c1-120)" | tee -a $ST
  rm -f $L/*.lp
done
