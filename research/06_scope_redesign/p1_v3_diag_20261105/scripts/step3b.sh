#!/bin/bash
# V3 DIAG step 3, second batch (presolve probes only; replaces the rest of step3a.sh, which ended with the OOM of call 14).
# Run protection: MemLimit 7 GB (hard, checked at allocation - the barrier ordering after a passed presolve stops with OUT_OF_MEMORY instead of
# the kernel OOM killer; the failing presolves needed <= 5.13 GB) + SoftMemLimit 6. Verdict from the Gurobi log: "infeasible or unbounded" ->
# INF_OR_UNBD; a "Presolved:" line without it -> presolve passed (status ITERATION_LIMIT / MEM_LIMIT / OUT_OF_MEMORY error after presolve).
#   F1_N_W1   native weights (s2_solve.main full-year path on the window: 3 h per snapshot) [0,56)  - the full-year mechanism on week 1
#   F1_J0130  Jan 1-30 [0,240), F1_J0231 Jan 2-31 [8,248) (runner TRUNCATE weighting) - length vs day
#   F1_W2..W5 January weeks [56,112) [112,168) [168,224) [224,248) (TRUNCATE weighting; week 1 = control C0)
set -u
. "$(dirname "$0")/common.sh"
verdict() { local L=$RUNROOT/$1/gurobi.linopy.log
  if grep -qi "infeasible or unbounded" "$L" 2>/dev/null; then echo INF_OR_UNBD
  elif grep -qi "^Model is infeasible" "$L" 2>/dev/null; then echo INFEASIBLE
  elif grep -qi "^Model is unbounded\|^Unbounded model" "$L" 2>/dev/null; then echo UNBOUNDED
  elif grep -q "^Presolved:" "$L" 2>/dev/null; then echo PRESOLVE_PASSED
  else echo UNDECIDED; fi; }
one() {   # id start len [native]
  bash "$S/build.sh" "$1" F1 "$2" "$3" "${4:-window}" || { log "STEP3B_STOP:$1:build failed"; return 1; }
  bash "$S/probe.sh" "$1" "$1" --protect MemLimit=7 --protect SoftMemLimit=6; local ex=$?
  [ $ex = 3 ] && { log "STEP3B_STOP:$1:no token route"; return 1; }
  local v; v=$(verdict "$1")
  log "VERDICT:$1:$v:probe_exit=$ex"
  if [ "$v" = PRESOLVE_PASSED ]; then rm -f "$RUNROOT/$1/split/problem.lp"; log "LP_REMOVED:$1:presolve passed"; else log "LP_KEPT:$1:$v"; fi
}
one F1_N_W1 0 56 native || exit 2
one F1_J0130 0 240 || exit 2
one F1_J0231 8 240 || exit 2
one F1_W2 56 56 || exit 2
one F1_W3 112 56 || exit 2
one F1_W4 168 56 || exit 2
one F1_W5 224 24 || exit 2
log "STEP3B_DONE:$(now)"
