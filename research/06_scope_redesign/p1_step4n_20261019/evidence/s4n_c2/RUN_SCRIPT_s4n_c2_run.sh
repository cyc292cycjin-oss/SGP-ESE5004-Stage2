#!/bin/bash
# S4N supplement 02 C2 (decision 119; user authorisation 2026-10-19 16:37 / ~16:55 SGT: at most 3 local 56x3h runs): profile pypsa_eur_default on the
# S4M-1 networks (2920x3h builds, --truncate 56): integrated STEPS, disconnected STEPS, integrated NZE - one run each, 30 min stop-loss, no retry,
# serial with >= 5 min between runs; STOP on the first non-optimal run (supplement 02 stop condition). Code: branch codex/s4n-calibration-20261019
# commit 7c4f97fe (config only). Starts only after NOT_BEFORE (epoch: instance licence deleted and the last cloud Gurobi session ended >= 5 min).
set -u
NOT_BEFORE=${1:?epoch}
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; cd $RM
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 GRB_LICENSE_FILE=/home/jin/gurobi.lic
B=results_project/s4m/s4m1/builds; S=results_project/s4n/s4n_c2; mkdir -p $S/solves; ST=$S/STATUS.txt
[ "$(git branch --show-current)" = "codex/s4n-calibration-20261019" ] || { echo "REFUSED: wrong branch" | tee -a $ST; exit 2; }
[ "$(git rev-parse --short=8 HEAD)" = "7c4f97fe" ] || { echo "REFUSED: HEAD is not 7c4f97fe" | tee -a $ST; exit 2; }
[ "$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" = 0 ] || { echo "REFUSED: dirty tree" | tee -a $ST; exit 2; }
while [ $(date +%s) -lt $NOT_BEFORE ]; do sleep 10; done
ps -eo cmd | grep -qE '[s]2_solve.py|[g]urobi_cl' && { echo "REFUSED: solver process running" | tee -a $ST; exit 2; }
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) branch:$(git branch --show-current) profile:pypsa_eur_default not_before:$NOT_BEFORE" >> $ST
AUTH="S4N supplement 02 C2 (decision 119; user 2026-10-19): profile calibration pypsa_eur_default (PyPSA-Eur v2025.07.0 gurobi-default), 56x3h on the S4M-1 networks, one run per scenario, stop-loss 30 min, no retry"
last_end=0
for spec in "cal_integrated:integrated:integrated" "cal_disconnected:disconnected:disconnected" "cal_integrated_nze:integrated_nze:integrated"; do
  IFS=: read tag bt sc <<< "$spec"
  if [ $last_end -gt 0 ]; then while [ $(( $(date +%s) - last_end )) -lt 300 ]; do sleep 5; done; echo "GAP_DONE_$tag:$(date -u +%Y-%m-%dT%H:%M:%SZ):$(( $(date +%s) - last_end ))s" >> $ST; fi
  net=$B/$bt/${sc}_2920_3h_unsolved.nc; d=$S/solves/$tag; mkdir -p $d
  echo "NET_$tag:$(sha256sum $net | cut -c1-16)" >> $ST
  ( exec setsid /usr/bin/time -v $PY scripts_project/s2_solve.py --network $net --scenario $sc --output $d --truncate 56 --label SMOKE_TEST_ONLY \
      --authorization "$AUTH; run $tag" --solver gurobi --solver-profile pypsa_eur_default --scaling on --time-limit 1750 --costs-table $B/$bt/costs_active_research.csv > $d.solve.log 2> $d.solve.err ) &
  pid=$!; start=$(date +%s); sleep 1; pg=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  echo "SOLVE_$tag:pid=$pid:pgid=$pg:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
  while kill -0 $pid 2>/dev/null; do sleep 10; if [ $(( $(date +%s) - start )) -ge 1800 ]; then echo "KILLED_30MIN_$tag" >> $ST; kill -TERM -- -$pg 2>/dev/null; sleep 20; kill -KILL -- -$pg 2>/dev/null; break; fi; done
  wait $pid 2>/dev/null; w=0; while pgrep -g $pg >/dev/null 2>&1 && [ $w -lt 120 ]; do sleep 1; w=$((w + 1)); done
  last_end=$(date +%s)
  cond=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition','none'))" $d/SOLVE_RECEIPT.json 2>/dev/null || echo none)
  tol=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('all_passed_solver_tolerances'))" $d/V5_GATES.json 2>/dev/null || echo none)
  echo "RUN_$tag:$cond:$(( last_end - start ))s:tol=$tol:$(grep -h 'Maximum resident' $d.solve.err | tr -s ' \t' ' '):end=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
  grep -viE "licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic" $d.solve.log > $d.solve_log_scrubbed.txt
  if [ "$cond" != "optimal" ]; then
    tail -60 $d/GUROBI_LOG_SCRUBBED.txt 2>/dev/null > $d/LOG_TAIL_NONOPTIMAL.txt; tail -60 $d.solve.err | grep -viE "licen[cs]e|registered|wls|academic|secret|token|accessid" > $d/STDERR_TAIL_NONOPTIMAL.txt
    echo "STOP_$tag:$cond (supplement 02 stop condition: a calibration run non-optimal; remaining runs not started, no retry)" >> $ST; break
  fi
done
echo "LAST_GUROBI_END:$(date -u +%Y-%m-%dT%H:%M:%SZ -d @$last_end)" >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
grep -v PROJ $ST
