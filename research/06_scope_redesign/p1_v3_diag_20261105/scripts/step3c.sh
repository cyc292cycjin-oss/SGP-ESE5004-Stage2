#!/bin/bash
# V3 DIAG step 3, third batch: the full-year weighting on a month. F1_N_M01 = January [0,248) with native weights (s2_solve.main's full-year path on
# the window: 3 h per snapshot, no set_representative_weights). The week with native weights (F1_N_W1) passed presolve; the full year (native) fails.
set -u
. "$(dirname "$0")/common.sh"
verdict() { local L=$RUNROOT/$1/gurobi.linopy.log
  if grep -qi "infeasible or unbounded" "$L" 2>/dev/null; then echo INF_OR_UNBD
  elif grep -qi "^Model is infeasible" "$L" 2>/dev/null; then echo INFEASIBLE
  elif grep -qi "^Model is unbounded\|^Unbounded model" "$L" 2>/dev/null; then echo UNBOUNDED
  elif grep -q "^Presolved:" "$L" 2>/dev/null; then echo PRESOLVE_PASSED
  else echo UNDECIDED; fi; }
one() {   # id start len how
  bash "$S/build.sh" "$1" F1 "$2" "$3" "${4:-window}" || { log "STEP3C_STOP:$1:build failed"; return 1; }
  bash "$S/probe.sh" "$1" "$1" --protect MemLimit=7 --protect SoftMemLimit=6; local ex=$?
  [ $ex = 3 ] && { log "STEP3C_STOP:$1:no token route"; return 1; }
  local v; v=$(verdict "$1")
  log "VERDICT:$1:$v:probe_exit=$ex"
  if [ "$v" = PRESOLVE_PASSED ]; then rm -f "$RUNROOT/$1/split/problem.lp"; log "LP_REMOVED:$1:presolve passed"; else log "LP_KEPT:$1:$v"; fi
}
for spec in "$@"; do IFS=: read -r id st len how <<< "$spec"; one "$id" "$st" "$len" "$how" || exit 2; done
log "STEP3C_DONE:$*:$(now)"
