#!/bin/bash
# S4A-4 smoke (S4A instruction S4A-4; decisions 70-73 and ledger L14-L16 authorised by the user 2026-10-16): both scenarios with the main
# settings (fuel_carbon_mode origin_neutral, profile_variant pypsa_eur, resource_classes 1, gem_additions, gem_fields), 56x3h, Gurobi
# formal_barrier + scaling. Stop-loss as S3B: 30 min wall clock per run (TimeLimit 1750 s), non-optimal -> log tail, no retry, no parameter change,
# no gap or crossover diagnostics (not named by the S4A instruction).
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s4a/smoke
mkdir -p $OUT/builds $OUT/solves
ST=$OUT/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD)" >> $ST
AUTH="S4A-4 smoke (S4A instruction S4A-4; decisions 70-73, ledger L14-L16, user authorization 2026-10-16): 56x3h smoke only, Gurobi formal_barrier, stop-loss 30 min, no retry"
for sc in integrated disconnected; do
  mkdir -p $OUT/builds/$sc
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/builds/$sc > $OUT/builds/${sc}_build.log 2> $OUT/builds/${sc}_build.err
  echo "BUILD_$sc:$?:$(grep -o '"status": "[A-Z_0-9]*"' $OUT/builds/$sc/${sc}_BUILD_RECEIPT.json | head -1)" >> $ST
done
for sc in integrated disconnected; do
  net=$OUT/builds/$sc/${sc}_2920_3h_unsolved.nc
  [ -f $net ] || { echo "SKIP_$sc:no build" >> $ST; continue; }
  mkdir -p $OUT/solves/$sc
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network $net --scenario $sc --output $OUT/solves/$sc --truncate 56 --label SMOKE_TEST_ONLY \
     --authorization "$AUTH; run $sc" --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 1750 \
     > $OUT/solves/${sc}_solve.log 2> $OUT/solves/${sc}_solve.err &
  pid=$!; start=$(date +%s)
  while kill -0 $pid 2>/dev/null; do
    sleep 15
    if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill $pid; sleep 5; kill -9 $pid 2>/dev/null; echo "KILLED_30MIN_$sc:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST; fi
  done
  wait $pid 2>/dev/null
  cond=$($PY -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('termination_condition','none'))" $OUT/solves/$sc/SOLVE_RECEIPT.json 2>/dev/null || echo none)
  echo "RUN_$sc:$cond:$(( $(date +%s) - start ))s:$(grep -h 'Maximum resident' $OUT/solves/${sc}_solve.err | tr -s ' ')" >> $ST
  if [ "$cond" != "optimal" ]; then tail -40 $OUT/solves/$sc/gurobi.linopy.log 2>/dev/null | grep -vi "license\|registered\|wls\|academic\|secret" > $OUT/solves/$sc/LOG_TAIL_NONOPTIMAL.txt; tail -40 $OUT/solves/${sc}_solve.err | grep -vi "license\|registered\|wls\|academic\|secret" > $OUT/solves/$sc/STDERR_TAIL_NONOPTIMAL.txt; fi
done
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
