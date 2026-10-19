#!/bin/bash
# S4L-2 continuation (user authorisation 2026-10-19 after the S4L report: "授权按修正后的清理规则（保护服务固定需求的生物质池）重跑清理后网络的 4 个运行
# （档案 A 与 crossover 档案 × 一体化 / 不互联，56×3h，各 30 分钟止损，不重试）"): the corrected cleaned network (results_project/s4l/s4l1, commit 2983d951)
# x {formal_barrier, formal_barrier_crossover} x {integrated, disconnected}. Serial, 30 min stop-loss, no retry, no parameter change; licence only via
# GRB_LICENSE_FILE. The S4K-network reference runs of the first matrix are linked in (not re-run) so the fixed comparison standard applies unchanged.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s4l/s4l2b; mkdir -p $OUT/solves
for t in s4k_A_integrated s4k_A_disconnected s4k_X_integrated s4k_X_disconnected; do [ -e $OUT/solves/$t ] || ln -s ../../s4l2/solves/$t $OUT/solves/$t; done
ST=$OUT/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" >> $ST
AUTH="S4L-2 continuation (user authorisation 2026-10-19 after the S4L report: corrected cleanup rule network, 4 runs: profile A and formal_barrier_crossover x integrated / disconnected, 56x3h, 30 min stop-loss, no retry)"
net_of() { echo results_project/s4l/s4l1/builds/$1/${1}_2920_3h_unsolved.nc; }
prof_of() { case "$1" in A) echo formal_barrier;; X) echo formal_barrier_crossover;; esac; }
run_watch() { local pr=$1 sc=$2; local tag=s4l_${pr}_${sc} d=$OUT/solves/s4l_${pr}_${sc}; local nc=$(net_of $sc) profile=$(prof_of $pr)
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
for pr in A X; do for sc in integrated disconnected; do c=$(run_watch $pr $sc | tail -1); [ "$c" = "optimal" ] || echo "NOT_OPTIMAL_s4l_${pr}_$sc:$c (recorded, no retry)" >> $ST; done; done
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
(cd scripts_project && $PY s4l_2_summary.py --run ../$OUT --s4k3 ../results_project/s4k/s4k3 > ../$OUT/summary.log 2>&1); echo "SUMMARY:$?" >> $ST
grep -v PROJ $ST
