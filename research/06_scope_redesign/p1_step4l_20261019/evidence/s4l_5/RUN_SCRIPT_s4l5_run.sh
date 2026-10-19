#!/bin/bash
# S4L-5 (user-authorised additional diagnostic, 2026-10-19): the 98 % biomass-cap diagnostic network (research.s2.industry.biomass_overflow_cap_share=0.98,
# no dust cleanup) solved with profile A, integrated and disconnected STEPS, 56x3h, 30 min stop-loss each, no retry. Waits for the S4L-2 continuation
# matrix (results_project/s4l/s4l2b) to finish first (one Gurobi session at a time; academic WLS). Then the S4L-2 summary over s4l2b + this arm.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s4l/s4l5; mkdir -p $OUT/solves
ST=$OUT/STATUS.txt
while ! grep -qE "^(DONE|STOP_)" results_project/s4l/s4l2b/STATUS.txt 2>/dev/null; do sleep 20; done
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l) after_s4l2b_done" >> $ST
AUTH="S4L-5 (user authorisation 2026-10-19 after the S4L report: biomass zero-slack diagnostic network, cap 98 % of the potential for the binding countries, remainder to methane by the decision-36 rule; profile A, integrated and disconnected, 56x3h, 30 min stop-loss, no retry; diagnostic only)"
run_watch() { local sc=$1; local tag=bio98_A_$sc d=$OUT/solves/bio98_A_$sc nc=$OUT/builds/$sc/${sc}_2920_3h_unsolved.nc
  [ -f $nc ] || { echo "SKIP_$tag:no network $nc" >> $ST; echo none; return; }
  mkdir -p $d
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network $nc --scenario $sc --output $d --truncate 56 --label SMOKE_TEST_ONLY \
     --authorization "$AUTH; run $tag" --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 1750 > $d.solve.log 2> $d.solve.err &
  local pid=$! start=$(date +%s)
  while kill -0 $pid 2>/dev/null; do sleep 15; if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill $pid; sleep 5; kill -9 $pid 2>/dev/null; echo "KILLED_30MIN_$tag" >> $ST; fi; done
  wait $pid 2>/dev/null
  local cond=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition','none'))" $d/SOLVE_RECEIPT.json 2>/dev/null || echo none)
  local tol=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('all_passed_solver_tolerances'))" $d/V5_GATES.json 2>/dev/null || echo none)
  echo "RUN_$tag:$cond:$(( $(date +%s) - start ))s:tol=$tol:$(grep -h 'Maximum resident' $d.solve.err | tr -s ' ')" >> $ST
  if [ "$cond" != "optimal" ]; then tail -40 $d/GUROBI_LOG_SCRUBBED.txt 2>/dev/null > $d/LOG_TAIL_NONOPTIMAL.txt; tail -40 $d.solve.err | grep -viE "licen[cs]e|registered|wls|academic|secret|token|accessid" > $d/STDERR_TAIL_NONOPTIMAL.txt; fi
  echo $cond
}
for sc in integrated disconnected; do c=$(run_watch $sc | tail -1); [ "$c" = "optimal" ] || echo "NOT_OPTIMAL_bio98_A_$sc:$c (recorded, no retry)" >> $ST; done
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
(cd scripts_project && $PY s4l_2_summary.py --run ../results_project/s4l/s4l2b --s4k3 ../results_project/s4k/s4k3 --extra bio98=../$OUT/solves > ../$OUT/summary.log 2>&1); echo "SUMMARY:$?" >> $ST
grep -v PROJ $ST
