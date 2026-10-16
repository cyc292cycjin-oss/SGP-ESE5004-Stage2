#!/bin/bash
# S4B-5 builds and smoke (S4B instruction v1 2026-10-16 16:45 SGT, section S4B-5; decisions 70-79 authorised 2026-10-16): builds of the
# integrated and disconnected main networks and of the two gap diagnostics with all S4B main settings (origin_neutral, calibrated_modern,
# resource_classes 3, S4B-0 to S4B-2 changes, typhoon_premium off), incl. the 365x24h daily networks for the cloud package (S4B-6);
# structural gap table; then 56x3h Gurobi formal_barrier + scaling: integrated main (must be OPTIMAL, else stop-loss), disconnected main
# (expected infeasible: any status is recorded, no stop-loss, S4B-5 item 2), disconnected gap diagnostic (must be OPTIMAL, else stop and
# report), integrated gap diagnostic (optional, S4B-5 item 2; only after the others passed). 30 min wall clock per run (TimeLimit 1750 s),
# no retry, no parameter change.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s4b/s4b5
mkdir -p $OUT/builds $OUT/solves $OUT/analysis
ST=$OUT/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" >> $ST
AUTH="S4B-5 smoke (S4B instruction v1 2026-10-16 16:45 SGT; decisions 70-79): 56x3h smoke only, Gurobi formal_barrier, stop-loss 30 min, no retry"
build() {   # $1 tag $2 scenario, extra args
  local tag=$1 sc=$2; shift 2
  mkdir -p $OUT/builds/$tag
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/builds/$tag "$@" > $OUT/builds/${tag}_build.log 2> $OUT/builds/${tag}_build.err
  echo "BUILD_$tag:$?:$(tail -1 $OUT/builds/${tag}_build.log | cut -c1-60):$(grep -h 'Maximum resident' $OUT/builds/${tag}_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/builds/${tag}_build.err | tr -s ' '):daily=$(ls $OUT/builds/$tag/*_365_24h_unsolved.nc 2>/dev/null | wc -l)" >> $ST
}
build integrated integrated
build disconnected disconnected
build disconnected_gap disconnected --gap-diagnostic
build integrated_gap integrated --gap-diagnostic
$PY scripts_project/s4b_structural_gap.py --network $OUT/builds/disconnected/disconnected_2920_3h_unsolved.nc --network $OUT/builds/integrated/integrated_2920_3h_unsolved.nc \
   --output $OUT/analysis/S4B5_STRUCTURAL_GAP_ANNUAL.json --csv $OUT/analysis/S4B5_STRUCTURAL_GAP_ANNUAL.csv > $OUT/analysis/structural_gap.log 2>&1
echo "STRUCTURAL:$?" >> $ST
run_watch() {   # $1 tag $2 network $3 scenario $4 label
  local tag=$1 net=$2 sc=$3 label=$4
  [ -f $net ] || { echo "SKIP_$tag:no build" >> $ST; echo none; return; }
  mkdir -p $OUT/solves/$tag
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network $net --scenario $sc --output $OUT/solves/$tag --truncate 56 --label $label \
     --authorization "$AUTH; run $tag" --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 1750 \
     > $OUT/solves/${tag}_solve.log 2> $OUT/solves/${tag}_solve.err &
  local pid=$! start=$(date +%s)
  while kill -0 $pid 2>/dev/null; do
    sleep 15
    if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill $pid; sleep 5; kill -9 $pid 2>/dev/null; echo "KILLED_30MIN_$tag:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST; fi
  done
  wait $pid 2>/dev/null
  local cond=$($PY -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('termination_condition','none'))" $OUT/solves/$tag/SOLVE_RECEIPT.json 2>/dev/null || echo none)
  echo "RUN_$tag:$cond:$(( $(date +%s) - start ))s:$(grep -h 'Maximum resident' $OUT/solves/${tag}_solve.err | tr -s ' ')" >> $ST
  if [ "$cond" != "optimal" ]; then tail -40 $OUT/solves/$tag/gurobi.linopy.log 2>/dev/null | grep -viE "licen[cs]e|registered|wls|academic|secret" > $OUT/solves/$tag/LOG_TAIL_NONOPTIMAL.txt; tail -40 $OUT/solves/${tag}_solve.err | grep -viE "licen[cs]e|registered|wls|academic|secret" > $OUT/solves/$tag/STDERR_TAIL_NONOPTIMAL.txt; fi
  echo $cond
}
c1=$(run_watch integrated $OUT/builds/integrated/integrated_2920_3h_unsolved.nc integrated SMOKE_TEST_ONLY | tail -1)
if [ "$c1" != "optimal" ]; then echo "STOP_LOSS_integrated:$c1" >> $ST; echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST; exit 0; fi
c2=$(run_watch disconnected $OUT/builds/disconnected/disconnected_2920_3h_unsolved.nc disconnected SMOKE_TEST_ONLY | tail -1)
echo "DISCONNECTED_MAIN_EXPECTED_INFEASIBLE:$c2" >> $ST
c3=$(run_watch disconnected_gap $OUT/builds/disconnected_gap/disconnected_gap_diagnostic_2920_3h_unsolved.nc disconnected GAP_DIAGNOSTIC | tail -1)
if [ "$c3" != "optimal" ]; then echo "STOP_gap_diagnostic_not_optimal:$c3" >> $ST; echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST; exit 0; fi
c4=$(run_watch integrated_gap $OUT/builds/integrated_gap/integrated_gap_diagnostic_2920_3h_unsolved.nc integrated GAP_DIAGNOSTIC | tail -1)
[ "$c4" != "optimal" ] && echo "STOP_integrated_gap_diagnostic_not_optimal:$c4" >> $ST
$PY scripts_project/s4b_5_summary.py --run $OUT --s4a results_project/s4a/smoke --s4b0 results_project/s4b/s4b0 > $OUT/analysis/summary.log 2>&1
echo "SUMMARY:$?" >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
