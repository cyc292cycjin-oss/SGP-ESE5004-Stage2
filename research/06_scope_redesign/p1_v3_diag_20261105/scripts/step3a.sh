#!/bin/bash
# V3 DIAG step 3, first batch (after months.sh): presolve probes only.
#   1. F1_M01 with DualReductions=0 (INFEASIBLE vs UNBOUNDED; b4_split_solve.py --measure, SMOKE_TEST_ONLY) on the kept problem.lp
#   2. two 240-snapshot windows of January: Jan 1-30 [0,240) and Jan 2-31 [8,248) - with Jan 1-31 [0,248) failing, both passing means the
#      verdict depends on the window length / weight and not on a day; one failing points at Jan 1 or Jan 31
#   3. January weeks (runner TRUNCATE weighting, 56 snapshots; week 1 = control C0): W2 [56,112), W3 [112,168), W4 [168,224), W5 [224,248)
set -u
. "$(dirname "$0")/common.sh"
one() {   # id start len
  bash "$S/build.sh" "$1" F1 "$2" "$3" || { log "STEP3A_STOP:$1:build failed"; return 1; }
  bash "$S/probe.sh" "$1" "$1" --protect SoftMemLimit=6; local ex=$?
  [ $ex = 3 ] && { log "STEP3A_STOP:$1:no token route"; return 1; }
  local st; st=$("$PY" -c "import json; print(json.load(open('$RUNROOT/$1/split/SPLIT_SOLVE.json')).get('gurobi_status_name',''))" 2>/dev/null)
  if [ "$st" = ITERATION_LIMIT ] || { [ "$st" = MEM_LIMIT ] && grep -q "^Presolved:" "$RUNROOT/$1/gurobi.linopy.log"; }; then rm -f "$RUNROOT/$1/split/problem.lp"; log "LP_REMOVED:$1:status=$st (presolve passed)"; else log "LP_KEPT:$1:status=$st"; fi
}
bash "$S/probe.sh" F1_M01 F1_M01_dr0 --measure DualReductions=0 --protect SoftMemLimit=6 || [ $? = 0 ]
one F1_J0130 0 240 || exit 2
one F1_J0231 8 240 || exit 2
one F1_W2 56 56 || exit 2
one F1_W3 112 56 || exit 2
one F1_W4 168 56 || exit 2
one F1_W5 224 24 || exit 2
log "STEP3A_DONE:$(now)"
