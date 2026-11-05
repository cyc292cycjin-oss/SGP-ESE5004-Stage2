#!/bin/bash
# V3.1 section 5.1: failure-window recheck on the FIXED code (2 Gurobi calls, presolve only; parameters and protection as V3 DIAG section 4 /
# calls 15-35: b4_split_solve.py --probe-ordering-only, --protect MemLimit=7 --protect SoftMemLimit=6). Pass = "Presolved:" in the Gurobi log
# and no infeasible / unbounded verdict. Also: LP rows of the window against the V3 DIAG build of the same window (expected difference
# = 82 metering links x window length - 1 row).
set -u
. "$(dirname "$0")/common.sh"
DIAG_EV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_diag_20261105/evidence/runs
verdict() { local L=$RUNROOT/$1/gurobi.linopy.log
  if grep -qi "infeasible or unbounded" "$L" 2>/dev/null; then echo INF_OR_UNBD
  elif grep -qi "^Model is infeasible" "$L" 2>/dev/null; then echo INFEASIBLE
  elif grep -qi "^Model is unbounded\|^Unbounded model" "$L" 2>/dev/null; then echo UNBOUNDED
  elif grep -q "^Presolved:" "$L" 2>/dev/null; then echo PRESOLVE_PASSED
  else echo UNDECIDED; fi; }
rows_of() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['num_row'], d['num_col'], d['nnz'])" "$1" 2>/dev/null || echo "? ? ?"; }
H=$(git -C "$REPO" rev-parse HEAD); DT=$(git -C "$REPO" status --porcelain --untracked-files=no | wc -l)
log "WIN_START:head=$H:dirty=$DT:$(now)"
[ "$DT" = 0 ] || { log "WIN_STOP:tracked changes in $REPO"; exit 2; }
one() {   # id F start len
  bash "$S/build.sh" "$1" "$2" "$3" "$4" window || { log "WIN_STOP:$1:build failed"; return 1; }
  bash "$S/probe.sh" "$1" "$1" --protect MemLimit=7 --protect SoftMemLimit=6; local ex=$?
  [ $ex = 3 ] && { log "WIN_STOP:$1:no token route"; return 1; }
  local v; v=$(verdict "$1")
  local pl; pl=$(grep -h "^Presolved:" "$RUNROOT/$1/gurobi.linopy.log" 2>/dev/null | tail -1)
  read -r r c z < <(rows_of "$RUNROOT/$1/lp/MATH_PROBLEM.json"); read -r r0 c0 z0 < <(rows_of "$DIAG_EV/$1/MATH_PROBLEM.json")
  local dr="?"; [ "$r" != "?" ] && [ "$r0" != "?" ] && dr=$(( r - r0 ))
  log "VERDICT:$1:$v:probe_exit=$ex:presolved_line=${pl:-none}:rows=$r:cols=$c:nnz=$z:diag_rows=$r0:diag_cols=$c0:diag_nnz=$z0:rows_minus_diag=$dr:expected=$(( 82 * $4 - 1 ))"
  if [ "$v" = PRESOLVE_PASSED ]; then rm -f "$RUNROOT/$1/split/problem.lp"; log "LP_REMOVED:$1:presolve passed"; else log "LP_KEPT:$1:$v"; fi
  echo "$v" > "$RUNROOT/$1/VERDICT.txt"
}
one F1_M01 F1 0 248 || exit 2
one F2_M02 F2 248 224 || exit 2
log "WIN_DONE:$(now)"
echo WIN_DONE
