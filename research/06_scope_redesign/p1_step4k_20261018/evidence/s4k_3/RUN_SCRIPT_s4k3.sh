#!/bin/bash
# S4K-3 smoke (S4K instruction S4K-3, decision 108, user 2026-10-18 22:37 SGT): 56x3h, Gurobi formal_barrier (profile A), 30 min stop-loss per run, no retry.
# Conditional diagnostic (authorised): if the integrated run is not optimal or fails all_passed_solver_tolerances -> stop the other runs and run ONE
# diagnostic: same network with network.ac_losses=none (DC and pipeline losses kept), integrated, then stop.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s4k/s4k3; mkdir -p $OUT/builds $OUT/solves
ST=$OUT/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l) profile:formal_barrier" >> $ST
AUTH="S4K-3 (decision 108, user 2026-10-18 22:37 SGT; S4K instruction S4K-3): AC linear loss proxy network: 56x3h smoke only, Gurobi formal_barrier, stop-loss 30 min, no retry"
build() { local tag=$1 sc=$2; shift 2; mkdir -p $OUT/builds/$tag
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/builds/$tag --no-daily "$@" > $OUT/builds/${tag}_build.log 2> $OUT/builds/${tag}_build.err
  echo "BUILD_$tag:$?:$(tail -1 $OUT/builds/${tag}_build.log | cut -c1-60):$(grep -h 'Maximum resident' $OUT/builds/${tag}_build.err | tr -s ' ')" >> $ST; }
run_watch() { local tag=$1; local sc=integrated; [ $tag = disconnected ] && sc=disconnected
  local net=$OUT/builds/$tag/${sc}_2920_3h_unsolved.nc d=$OUT/solves/$tag
  [ -f $net ] || { echo "SKIP_$tag:no build" >> $ST; echo none; return; }
  mkdir -p $d
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network $net --scenario $sc --output $d --truncate 56 --label SMOKE_TEST_ONLY \
     --authorization "$AUTH; run $tag" --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 1750 > $d.solve.log 2> $d.solve.err &
  local pid=$! start=$(date +%s)
  while kill -0 $pid 2>/dev/null; do sleep 15; if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill $pid; sleep 5; kill -9 $pid 2>/dev/null; echo "KILLED_30MIN_$tag" >> $ST; fi; done
  wait $pid 2>/dev/null
  local cond=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition','none'))" $d/SOLVE_RECEIPT.json 2>/dev/null || echo none)
  echo "RUN_$tag:$cond:$(( $(date +%s) - start ))s:$(grep -h 'Maximum resident' $d.solve.err | tr -s ' ')" >> $ST
  if [ "$cond" != "optimal" ]; then tail -40 $d/GUROBI_LOG_SCRUBBED.txt 2>/dev/null > $d/LOG_TAIL_NONOPTIMAL.txt; tail -40 $d.solve.err | grep -viE "licen[cs]e|registered|wls|academic|secret|token|accessid" > $d/STDERR_TAIL_NONOPTIMAL.txt; fi
  echo $cond
}
tol_of() { $PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('all_passed_solver_tolerances'))" $OUT/solves/$1/V5_GATES.json 2>/dev/null || echo none; }
build integrated integrated
build disconnected disconnected
build integrated_nze integrated --override fuels.price_scenario=nze
c=$(run_watch integrated | tail -1); tol=$(tol_of integrated); echo "GATE_integrated:termination=$c:all_passed_solver_tolerances=$tol" >> $ST
if [ "$c" != "optimal" ] || [ "$tol" != "True" ]; then
  echo "STOP_integrated:$c:$tol -> conditional diagnostic network.ac_losses=none (1 run), then stop" >> $ST
  build integrated_noac integrated --override network.ac_losses=none
  AUTH="$AUTH; conditional diagnostic authorised in S4K-3 (network.ac_losses=none, DC and pipeline losses kept)"
  r=$(run_watch integrated_noac | tail -1); tl=$(tol_of integrated_noac); echo "GATE_integrated_noac:termination=$r:all_passed_solver_tolerances=$tl" >> $ST
  echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST; grep -v PROJ $ST; exit 1
fi
echo "PASSED_integrated -> disconnected and integrated_nze" >> $ST
for t in disconnected integrated_nze; do r=$(run_watch $t | tail -1); tl=$(tol_of $t); echo "GATE_$t:termination=$r:all_passed_solver_tolerances=$tl" >> $ST
  { [ "$r" != "optimal" ] || [ "$tl" != "True" ]; } && echo "NOT_PASSED_$t:$r:$tl (recorded, no retry; S4K stop condition)" >> $ST; done
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
(cd scripts_project && $PY s4k_3_summary.py --run ../$OUT --ref-j ../results_project/s4j/s4j6b --ref-h ../results_project/s4h/s4h3 > ../$OUT/summary.log 2>&1); echo "SUMMARY:$?" >> $ST
grep -v PROJ $ST
