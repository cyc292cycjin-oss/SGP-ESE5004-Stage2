#!/bin/bash
# S4O-3 (S4O instruction v1; user authorisation 2026-10-19 ~20:00 SGT: "S4O-1 至 S4O-5 的本机部分（含 S4O-3 的 3 次本机 56×3h 运行）"):
# local calibration re-check of the FINAL production profile pypsa_eur_default (Threads 8, capitalised keys; decision 120) on the S4M-1 networks
# (2920x3h builds, --truncate 56): integrated STEPS, disconnected STEPS, integrated NZE - one run each, 30 min stop-loss, no retry, serial with
# >= 5 min between the end of one solve and the start of the next; STOP on the first non-optimal run (S4O-3 point 4). The profile is NOT passed on
# the command line: the run uses the configured default research.solver.profile (checked in the receipt). After every solve the pipeline C1 step
# (l23_violation_analysis.py + scripts_project/s4o_c1_precision.py run, Python only, no licence); after the disconnected run the batch reference
# (this 56x3h batch's disconnected - integrated) and the re-grading of both STEPS runs; NZE uses the batch reference. Code: branch
# codex/s4o-production-20261019 at the commit given as $1 (clean tree).
set -u
WANT=${1:?commit (8 chars)}
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; cd $RM
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 GRB_LICENSE_FILE=/home/jin/gurobi.lic
B=results_project/s4m/s4m1/builds; S=results_project/s4o/s4o3; mkdir -p $S/solves; ST=$S/STATUS.txt
[ "$(git branch --show-current)" = "codex/s4o-production-20261019" ] || { echo "REFUSED: wrong branch" | tee -a $ST; exit 2; }
[ "$(git rev-parse --short=8 HEAD)" = "$WANT" ] || { echo "REFUSED: HEAD is not $WANT" | tee -a $ST; exit 2; }
[ "$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" = 0 ] || { echo "REFUSED: dirty tree" | tee -a $ST; exit 2; }
ps -eo cmd | grep -qE '[s]2_solve.py|[g]urobi_cl' && { echo "REFUSED: solver process running" | tee -a $ST; exit 2; }
DEF=$($PY -c "import yaml; print(yaml.safe_load(open('configs/research/baseline.yaml'))['research']['solver']['profile'])")
[ "$DEF" = pypsa_eur_default ] || { echo "REFUSED: default profile is $DEF" | tee -a $ST; exit 2; }
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) branch:$(git branch --show-current) default_profile:$DEF" >> $ST
AUTH="S4O-3 (decision 120; user 2026-10-19 ~20:00 SGT): local calibration re-check of the final production profile pypsa_eur_default, 56x3h on the S4M-1 networks, one run per scenario, stop-loss 30 min, no retry"
c1() {   # $1 tag $2 network $3 scenario
  local d=$S/solves/$1 ref=()
  [ -f $S/BATCH_REFERENCE.json ] && ref=(--reference $S/BATCH_REFERENCE.json)
  [ -f $d/solution/X.npy ] && env -u GRB_LICENSE_FILE /usr/bin/time -v $PY scripts_project/l23_violation_analysis.py --repo $RM --solve-dir $d --network $2 --scenario $3 --truncate 56 --label SMOKE_TEST_ONLY --out $d/VIOLATIONS.json > $d.c1_va.log 2> $d.c1_va.err
  env -u GRB_LICENSE_FILE /usr/bin/time -v $PY scripts_project/s4o_c1_precision.py run --repo $RM --solve-dir $d --network $2 --scenario $3 --truncate 56 --label SMOKE_TEST_ONLY --violations $d/VIOLATIONS.json ${ref[@]+"${ref[@]}"} > $d.c1.log 2> $d.c1.err
  echo "PRECISION_$1:exit=$?:$(tail -1 $d.c1.log | cut -c1-260):$(grep -h 'Maximum resident' $d.c1.err | tr -s ' \t' ' ')" >> $ST
}
last_end=0
for spec in "s4o_integrated:integrated:integrated" "s4o_disconnected:disconnected:disconnected" "s4o_integrated_nze:integrated_nze:integrated"; do
  IFS=: read tag bt sc <<< "$spec"
  if [ $last_end -gt 0 ]; then while [ $(( $(date +%s) - last_end )) -lt 300 ]; do sleep 5; done; echo "GAP_DONE_$tag:$(date -u +%Y-%m-%dT%H:%M:%SZ):$(( $(date +%s) - last_end ))s" >> $ST; fi
  ps -eo cmd | grep -qE '[s]2_solve.py|[g]urobi_cl' && { echo "REFUSED_$tag: solver process running" >> $ST; break; }
  net=$B/$bt/${sc}_2920_3h_unsolved.nc; d=$S/solves/$tag; mkdir -p $d
  echo "NET_$tag:$(sha256sum $net | cut -c1-16)" >> $ST
  ( exec setsid /usr/bin/time -v $PY scripts_project/s2_solve.py --network $net --scenario $sc --output $d --truncate 56 --label SMOKE_TEST_ONLY \
      --authorization "$AUTH; run $tag" --solver gurobi --scaling on --time-limit 1750 --costs-table $B/$bt/costs_active_research.csv > $d.solve.log 2> $d.solve.err ) &
  pid=$!; start=$(date +%s); sleep 1; pg=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  echo "SOLVE_$tag:pid=$pid:pgid=$pg:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
  while kill -0 $pid 2>/dev/null; do sleep 10; if [ $(( $(date +%s) - start )) -ge 1800 ]; then echo "KILLED_30MIN_$tag" >> $ST; kill -TERM -- -$pg 2>/dev/null; sleep 20; kill -KILL -- -$pg 2>/dev/null; break; fi; done
  wait $pid 2>/dev/null; w=0; while pgrep -g $pg >/dev/null 2>&1 && [ $w -lt 120 ]; do sleep 1; w=$((w + 1)); done
  last_end=$(date +%s)
  cond=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition','none'))" $d/SOLVE_RECEIPT.json 2>/dev/null || echo none)
  prof=$($PY -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('solver_profile'), r.get('solver_parameters',{}).get('Threads'), r.get('solver_parameters',{}).get('Crossover'), r.get('solver_parameters',{}).get('BarConvTol'))" $d/SOLVE_RECEIPT.json 2>/dev/null)
  tol=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('all_passed_solver_tolerances'))" $d/V5_GATES.json 2>/dev/null || echo none)
  intr=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('interior_solution'))" $d/INTERIOR_CHECKS.json 2>/dev/null || echo none)
  echo "RUN_$tag:$cond:$(( last_end - start ))s:profile=${prof// /,}:interior=$intr:tol=$tol:$(grep -h 'Maximum resident' $d.solve.err | tr -s ' \t' ' '):end=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
  grep -viE "licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic" $d.solve.log > $d.solve_log_scrubbed.txt
  if [ "$cond" != "optimal" ]; then
    tail -60 $d/GUROBI_LOG_SCRUBBED.txt 2>/dev/null > $d/LOG_TAIL_NONOPTIMAL.txt; tail -60 $d.solve.err | grep -viE "licen[cs]e|registered|wls|academic|secret|token|accessid" > $d/STDERR_TAIL_NONOPTIMAL.txt
    c1 $tag $net $sc
    echo "STOP_$tag:$cond (S4O-3 point 4: a run non-optimal; remaining runs not started, no retry; S4O-4 not entered)" >> $ST; break
  fi
  c1 $tag $net $sc
  if [ $tag = s4o_disconnected ]; then
    env -u GRB_LICENSE_FILE $PY scripts_project/s4o_c1_precision.py reference --integrated $S/solves/s4o_integrated --disconnected $S/solves/s4o_disconnected --out $S/BATCH_REFERENCE.json > $S/reference.log 2>&1; echo "BATCH_REFERENCE:exit=$?" >> $ST
    for t in s4o_integrated s4o_disconnected; do
      env -u GRB_LICENSE_FILE $PY scripts_project/s4o_c1_precision.py regrade --solve-dir $S/solves/$t --reference $S/BATCH_REFERENCE.json > $S/solves/$t.regrade.log 2>&1; echo "REGRADE_$t:exit=$?:$(tail -1 $S/solves/$t.regrade.log | cut -c1-260)" >> $ST
    done
  fi
done
echo "LAST_GUROBI_END:$(date -u +%Y-%m-%dT%H:%M:%SZ -d @$last_end)" >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
grep -v PROJ $ST
