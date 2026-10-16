#!/bin/bash
# S3B smoke (instruction section 3; decisions 66-69 authorised 2026-10-16 10:45 SGT): 2 scenarios x 2 carbon modes, 56x3h, decision-58 weights,
# Gurobi formal_barrier + scaling; gap_diagnostic for the disconnected scenario if infeasible (integrated only if exactly infeasible);
# crossover_diagnostic of the integrated main run. Stop-loss: 30 min wall clock per run (TimeLimit 1750 s), non-optimal -> log tail, no retry,
# no parameter change (INF_OR_UNBD inside the crossover diagnostic is expected and recorded only).
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s3b/smoke
mkdir -p $OUT/builds $OUT/solves
ST=$OUT/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD)" >> $ST
AUTH="S3B smoke (instruction section 3; decisions 66-69, user authorization 2026-10-16 10:45 SGT): 56x3h smoke only, Gurobi formal_barrier, stop-loss 30 min, no retry"

build() {   # $1 tag $2 scenario $3 extra args
  local tag=$1 sc=$2; shift 2
  if [ ! -f $OUT/builds/$tag/${sc}_2920_3h_unsolved.nc ] && [ ! -f $OUT/builds/$tag/${sc}_gap_diagnostic_2920_3h_unsolved.nc ]; then
    mkdir -p $OUT/builds/$tag
    /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/builds/$tag "$@" > $OUT/builds/${tag}_build.log 2> $OUT/builds/${tag}_build.err
    echo "BUILD_$tag:$?" >> $ST
  fi
}

run_watch() {   # $1 tag $2 network $3 scenario $4 profile $5 label
  local tag=$1 net=$2 sc=$3 prof=$4 label=$5
  mkdir -p $OUT/solves/$tag
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network $net --scenario $sc --output $OUT/solves/$tag --truncate 56 --label $label \
     --authorization "$AUTH; run $tag" --solver gurobi --solver-profile $prof --scaling on --time-limit 1750 \
     > $OUT/solves/${tag}_solve.log 2> $OUT/solves/${tag}_solve.err &
  local pid=$! start=$(date +%s)
  while kill -0 $pid 2>/dev/null; do
    sleep 15
    if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill $pid; sleep 5; kill -9 $pid 2>/dev/null; echo "KILLED_30MIN_$tag:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST; fi
  done
  wait $pid 2>/dev/null
  local cond=$($PY -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('termination_condition','none'))" $OUT/solves/$tag/SOLVE_RECEIPT.json 2>/dev/null || echo none)
  echo "RUN_$tag:$cond:$(( $(date +%s) - start ))s" >> $ST
  if [ "$cond" != "optimal" ]; then tail -40 $OUT/solves/$tag/gurobi.linopy.log 2>/dev/null | grep -vi "license\|registered\|wls\|academic\|secret" > $OUT/solves/$tag/LOG_TAIL_NONOPTIMAL.txt; tail -40 $OUT/solves/${tag}_solve.err | grep -vi "license\|registered\|wls\|academic\|secret" > $OUT/solves/$tag/STDERR_TAIL_NONOPTIMAL.txt; fi
  echo $cond
}

# 1. builds
build integrated integrated
build disconnected disconnected
build pc_integrated integrated --override s3.fuel_carbon_mode=producer_credit
build pc_disconnected disconnected --override s3.fuel_carbon_mode=producer_credit
$PY scripts_project/s2_structural_gap.py --network $OUT/builds/integrated/integrated_2920_3h_unsolved.nc --network $OUT/builds/disconnected/disconnected_2920_3h_unsolved.nc --output $OUT/S3B_STRUCTURAL_GAP_ANNUAL.json > $OUT/builds/structural_gap.log 2>&1
echo "GAPTABLE:$?" >> $ST

# 2. smokes and gap diagnostics
for tag in integrated disconnected pc_integrated pc_disconnected; do
  sc=${tag#pc_}
  [ -f $OUT/builds/$tag/${sc}_2920_3h_unsolved.nc ] || { echo "SKIP_$tag:no build" >> $ST; continue; }
  c=$(run_watch $tag $OUT/builds/$tag/${sc}_2920_3h_unsolved.nc $sc formal_barrier SMOKE_TEST_ONLY)
  gap=no
  if [ "$sc" = "disconnected" ] && { [ "$c" = "infeasible" ] || [ "$c" = "infeasible_or_unbounded" ]; }; then gap=yes; fi
  if [ "$sc" = "integrated" ] && [ "$c" = "infeasible" ]; then gap=yes; fi
  if [ "$gap" = "yes" ]; then
    ov=""; [ "${tag#pc_}" != "$tag" ] && ov="--override s3.fuel_carbon_mode=producer_credit"
    build ${tag}_gap $sc --gap-diagnostic $ov
    if [ -f $OUT/builds/${tag}_gap/${sc}_gap_diagnostic_2920_3h_unsolved.nc ]; then
      run_watch ${tag}_gap $OUT/builds/${tag}_gap/${sc}_gap_diagnostic_2920_3h_unsolved.nc $sc formal_barrier GAP_DIAGNOSTIC > /dev/null
    fi
  else
    echo "GAP_$tag:not run (condition $c)" >> $ST
  fi
done

# 3. crossover diagnostic of the integrated main run
if grep -q "^RUN_integrated:optimal" $ST; then
  run_watch integrated_crossover $OUT/builds/integrated/integrated_2920_3h_unsolved.nc integrated crossover_diagnostic SMOKE_TEST_ONLY > /dev/null
else
  echo "CROSSOVER_DIAG:skipped (integrated main not optimal)" >> $ST
fi
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
