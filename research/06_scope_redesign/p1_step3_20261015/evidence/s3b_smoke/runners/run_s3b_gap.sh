#!/bin/bash
# S3B smoke section 3.3: the instruction asks for gap_diagnostic on the disconnected scenario (expected structurally infeasible). The disconnected
# smokes ended NUMERIC ("Numerical trouble encountered", not certified infeasible), so the main runner (conservative rule: gap only after an
# infeasible status) did not start them. This runner builds and solves the two disconnected gap_diagnostic LPs once each - a different LP with
# penalised slack columns, not a retry of the smoke; same formal_barrier profile, same 30-min stop-loss, no retry, no parameter change.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s3b/smoke
ST=$OUT/STATUS.txt
echo "GAP_RUNNER_START:$(date -u +%Y-%m-%dT%H:%M:%SZ) (instruction 3.3: disconnected gap_diagnostic; smokes ended NUMERIC)" >> $ST
AUTH="S3B smoke (instruction section 3.3; decisions 66-69, user authorization 2026-10-16 10:45 SGT): disconnected gap_diagnostic 56x3h, Gurobi formal_barrier, stop-loss 30 min, no retry"
for tag in disconnected pc_disconnected; do
  sc=disconnected; g=${tag}_gap; ov=""; [ "$tag" = pc_disconnected ] && ov="--override s3.fuel_carbon_mode=producer_credit"
  mkdir -p $OUT/builds/$g
  if [ ! -f $OUT/builds/$g/${sc}_gap_diagnostic_2920_3h_unsolved.nc ]; then
    /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/builds/$g --gap-diagnostic $ov > $OUT/builds/${g}_build.log 2> $OUT/builds/${g}_build.err
    echo "BUILD_$g:$?" >> $ST
  fi
  [ -f $OUT/builds/$g/${sc}_gap_diagnostic_2920_3h_unsolved.nc ] || continue
  mkdir -p $OUT/solves/$g
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/builds/$g/${sc}_gap_diagnostic_2920_3h_unsolved.nc --scenario $sc --output $OUT/solves/$g --truncate 56 --label GAP_DIAGNOSTIC \
     --authorization "$AUTH; run $g" --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 1750 > $OUT/solves/${g}_solve.log 2> $OUT/solves/${g}_solve.err &
  pid=$!; start=$(date +%s)
  while kill -0 $pid 2>/dev/null; do
    sleep 15
    if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill $pid; sleep 5; kill -9 $pid 2>/dev/null; echo "KILLED_30MIN_$g:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST; fi
  done
  wait $pid 2>/dev/null
  cond=$($PY -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('termination_condition','none'))" $OUT/solves/$g/SOLVE_RECEIPT.json 2>/dev/null || echo none)
  echo "RUN_$g:$cond:$(( $(date +%s) - start ))s" >> $ST
  if [ "$cond" != "optimal" ]; then tail -40 $OUT/solves/$g/gurobi.linopy.log 2>/dev/null | grep -vi "license\|registered\|wls\|academic\|secret" > $OUT/solves/$g/LOG_TAIL_NONOPTIMAL.txt; fi
done
echo "GAP_RUNNER_DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
