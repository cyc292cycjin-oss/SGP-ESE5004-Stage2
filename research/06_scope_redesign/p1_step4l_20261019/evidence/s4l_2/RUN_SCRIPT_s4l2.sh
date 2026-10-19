#!/bin/bash
# S4L-2 diagnostic matrix (S4L instruction S4L-2, decision 113 (2); user authorisation 2026-10-19 09:57 SGT covers these 8 local 56x3h runs):
# {S4K-3 network, S4L-1 cleaned network} x {formal_barrier (profile A), formal_barrier_crossover} x {integrated STEPS, disconnected STEPS}.
# Serial (academic WLS licence: at most 2 sessions; only one here), 30 min stop-loss per run (TimeLimit 1,750 s, hard kill 1,800 s), no retry,
# no parameter change. Licence only via GRB_LICENSE_FILE (never read, copied or printed). The comparison standard is fixed in the registry
# fragment s4l_2 and the progress file before this script starts.
# Stop rule (S4L stop conditions): if a S4K-network + profile-A run (the reference, converged in S4K-3) ends non-optimal, stop the matrix.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s4l/s4l2; mkdir -p $OUT/solves
ST=$OUT/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" >> $ST
AUTH="S4L-2 (decision 113 (2), user 2026-10-19 09:57 SGT; S4L instruction S4L-2): 56x3h diagnostic matrix, 8 runs, Gurobi formal_barrier | formal_barrier_crossover, stop-loss 30 min, no retry"
net_of() { case "$1" in s4k) echo results_project/s4k/s4k3/builds/$2/${2}_2920_3h_unsolved.nc;; s4l) echo results_project/s4l/s4l1/builds/$2/${2}_2920_3h_unsolved.nc;; esac; }
prof_of() { case "$1" in A) echo formal_barrier;; X) echo formal_barrier_crossover;; esac; }
run_watch() { local net=$1 pr=$2 sc=$3; local tag=${net}_${pr}_${sc} d=$OUT/solves/${net}_${pr}_${sc}; local nc=$(net_of $net $sc) profile=$(prof_of $pr)
  [ -f $nc ] || { echo "SKIP_$tag:no network $nc" >> $ST; echo none; return; }
  mkdir -p $d
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network $nc --scenario $sc --output $d --truncate 56 --label SMOKE_TEST_ONLY \
     --authorization "$AUTH; run $tag" --solver gurobi --solver-profile $profile --scaling on --time-limit 1750 > $d.solve.log 2> $d.solve.err &
  local pid=$! start=$(date +%s)
  while kill -0 $pid 2>/dev/null; do sleep 15; if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill $pid; sleep 5; kill -9 $pid 2>/dev/null; echo "KILLED_30MIN_$tag" >> $ST; fi; done
  wait $pid 2>/dev/null
  local cond=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition','none'))" $d/SOLVE_RECEIPT.json 2>/dev/null || echo none)
  local tol=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('all_passed_solver_tolerances'))" $d/V5_GATES.json 2>/dev/null || echo none)
  echo "RUN_$tag:$cond:$(( $(date +%s) - start ))s:tol=$tol:$(grep -h 'Maximum resident' $d.solve.err | tr -s ' ')" >> $ST
  if [ "$cond" != "optimal" ]; then tail -40 $d/GUROBI_LOG_SCRUBBED.txt 2>/dev/null > $d/LOG_TAIL_NONOPTIMAL.txt; tail -40 $d.solve.err | grep -viE "licen[cs]e|registered|wls|academic|secret|token|accessid" > $d/STDERR_TAIL_NONOPTIMAL.txt; fi
  echo $cond
}
for sc in integrated disconnected; do
  c=$(run_watch s4k A $sc | tail -1)
  if [ "$c" != "optimal" ]; then echo "STOP_s4k_A_$sc:$c (reference run not optimal: S4L stop condition, matrix stopped, no retry)" >> $ST; echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST; grep -v PROJ $ST; exit 1; fi
done
for combo in "s4k X" "s4l A" "s4l X"; do set -- $combo
  for sc in integrated disconnected; do c=$(run_watch $1 $2 $sc | tail -1); [ "$c" = "optimal" ] || echo "NOT_OPTIMAL_${1}_${2}_$sc:$c (recorded, no retry)" >> $ST; done
done
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
(cd scripts_project && $PY s4l_2_summary.py --run ../$OUT --s4k3 ../results_project/s4k/s4k3 > ../$OUT/summary.log 2>&1); echo "SUMMARY:$?" >> $ST
grep -v PROJ $ST
