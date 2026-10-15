#!/bin/bash
# S3-7 (decision 65) with the stop-loss rule (working principle 6): every Gurobi run is killed after 30 min wall-clock; non-optimal
# statuses (NUMERIC, SUBOPTIMAL, INF_OR_UNBD, time limit, ...) are recorded with the log tail and never retried; gap_diagnostic only
# for an exact "infeasible" termination.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s3_7/gurobi
AUTH="decision 65 (user authorization 2026-10-16): Gurobi 12.0.3 WLS academic licence, 56x3h smoke both carbon modes x both scenarios, gap_diagnostic if infeasible; stop-loss 30 min, no retry; smoke only"
LIMIT=1800
mkdir -p $OUT/smoke $OUT/gap_diagnostic

watch_pid() {   # $1 pid, $2 tag, $3 logdir : kill after LIMIT seconds wall-clock
  local pid=$1 tag=$2 logdir=$3 start=$(date +%s)
  while kill -0 $pid 2>/dev/null; do
    sleep 15
    if [ $(( $(date +%s) - start )) -ge $LIMIT ]; then
      kill $pid 2>/dev/null; sleep 5; kill -9 $pid 2>/dev/null
      echo "KILLED_30MIN_$tag:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $OUT/STATUS.txt
      tail -25 $logdir/gurobi.linopy.log 2>/dev/null | grep -vi "license\|registered\|wls\|academic\|secret" > $logdir/LOG_TAIL_AT_STOP.txt
      return 1
    fi
  done
  return 0
}

condition_of() {   # $1 receipt
  $PY -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('termination_condition','none'))" "$1" 2>/dev/null || echo none
}

# 0. the integrated run already started by run_s3_7g.sh (parent killed): adopt it under the watchdog
pid=$(pgrep -f "s2_solve.py --network results_project/s3_7/integrated/integrated_2920_3h_unsolved.nc" | head -1)
if [ -n "$pid" ]; then
  start_epoch=$(stat -c %Y $OUT/smoke/integrated/SOLVE_RECEIPT.json 2>/dev/null || date +%s)
  # the receipt is first written right before the solve; use it as the start reference
  while kill -0 $pid 2>/dev/null; do
    sleep 15
    if [ $(( $(date +%s) - start_epoch )) -ge $LIMIT ]; then
      kill $pid 2>/dev/null; sleep 5; kill -9 $pid 2>/dev/null
      echo "KILLED_30MIN_integrated:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $OUT/STATUS.txt
      tail -25 $OUT/smoke/integrated/gurobi.linopy.log 2>/dev/null | grep -vi "license\|registered\|wls\|academic\|secret" > $OUT/smoke/integrated/LOG_TAIL_AT_STOP.txt
      break
    fi
  done
  echo "GSMOKE_integrated:$(condition_of $OUT/smoke/integrated/SOLVE_RECEIPT.json)" >> $OUT/STATUS.txt
fi

run_one() {   # $1 tag, $2 kind (smoke|gap_diagnostic)
  local tag=$1 kind=$2 sc=${1#pc_} ov="" net label
  if [ "$tag" != "$sc" ]; then ov="--override s3.fuel_carbon_mode=producer_credit"; fi
  if [ "$kind" = "smoke" ]; then net=results_project/s3_7/$tag/${sc}_2920_3h_unsolved.nc; label=SMOKE_TEST_ONLY; else net=results_project/s3_7/${tag}_gap/${sc}_gap_diagnostic_2920_3h_unsolved.nc; label=GAP_DIAGNOSTIC; fi
  mkdir -p $OUT/$kind/$tag
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network $net --scenario $sc --output $OUT/$kind/$tag --truncate 56 --label $label --authorization "$AUTH" --solver gurobi --time-limit 1750 > $OUT/$kind/${tag}_solve.log 2> $OUT/$kind/${tag}_solve.err &
  local pid=$!
  watch_pid $pid "${kind}_${tag}" $OUT/$kind/$tag
  wait $pid 2>/dev/null
  local cond=$(condition_of $OUT/$kind/$tag/SOLVE_RECEIPT.json)
  echo "$( [ $kind = smoke ] && echo GSMOKE || echo GGAP )_$tag:$cond" >> $OUT/STATUS.txt
  if [ "$cond" != "optimal" ] && [ "$cond" != "infeasible" ]; then
    tail -25 $OUT/$kind/$tag/gurobi.linopy.log 2>/dev/null | grep -vi "license\|registered\|wls\|academic\|secret" > $OUT/$kind/$tag/LOG_TAIL_NONOPTIMAL.txt
  fi
  echo $cond
}

for tag in integrated disconnected pc_integrated pc_disconnected; do
  sc=${tag#pc_}; ov=""; if [ "$tag" != "$sc" ]; then ov="--override s3.fuel_carbon_mode=producer_credit"; fi
  if [ "$tag" = "integrated" ]; then cond=$(condition_of $OUT/smoke/integrated/SOLVE_RECEIPT.json); else cond=$(run_one $tag smoke); fi
  if [ "$cond" = "infeasible" ]; then
    if [ ! -f results_project/s3_7/${tag}_gap/${sc}_gap_diagnostic_2920_3h_unsolved.nc ]; then
      $PY scripts_project/s2_network.py --scenario $sc --output results_project/s3_7/${tag}_gap --gap-diagnostic $ov > results_project/s3_7/${tag}_gap_build.log 2> results_project/s3_7/${tag}_gap_build.err
      echo "GAPBUILD_$tag:$?" >> $OUT/STATUS.txt
    fi
    run_one $tag gap_diagnostic > /dev/null
  else
    echo "GGAP_$tag:skipped (smoke condition $cond)" >> $OUT/STATUS.txt
  fi
done
echo "DONE" >> $OUT/STATUS.txt
