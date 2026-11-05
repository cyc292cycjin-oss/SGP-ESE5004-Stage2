#!/bin/bash
# V3 DIAG step 3, fourth batch: presolve sensitivity on the kept F1_M01 problem.lp (INF_OR_UNBD with the profile; presolve passed with
# DualReductions=0). Measurement overrides only (b4_split_solve.py --measure, SMOKE_TEST_ONLY), presolve only (BarIterLimit 0), one Gurobi call each.
#   F1_M01_nf3  NumericFocus=3   F1_M01_agg0  Aggregate=0   F1_M01_pre1  Presolve=1
set -u
. "$(dirname "$0")/common.sh"
verdict() { local L=$RUNROOT/$1/gurobi.linopy.log
  if grep -qi "infeasible or unbounded" "$L" 2>/dev/null; then echo INF_OR_UNBD
  elif grep -qi "^Model is infeasible" "$L" 2>/dev/null; then echo INFEASIBLE
  elif grep -qi "^Model is unbounded\|^Unbounded model" "$L" 2>/dev/null; then echo UNBOUNDED
  elif grep -q "^Presolved:" "$L" 2>/dev/null; then echo PRESOLVE_PASSED
  else echo UNDECIDED; fi; }
for spec in F1_M01_nf3:NumericFocus=3 F1_M01_agg0:Aggregate=0 F1_M01_pre1:Presolve=1; do
  id=${spec%%:*}; kv=${spec#*:}
  bash "$S/probe.sh" F1_M01 "$id" --measure "$kv" --protect MemLimit=7 --protect SoftMemLimit=6; ex=$?
  [ $ex = 3 ] && { log "STEP3D_STOP:$id:no token route"; exit 2; }
  log "VERDICT:$id:$(verdict "$id"):probe_exit=$ex:$kv"
done
log "STEP3D_DONE:$(now)"
