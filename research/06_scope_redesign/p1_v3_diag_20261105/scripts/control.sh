#!/bin/bash
# V3 DIAG step 1 (control): F1 first 56 snapshots exactly as the runner's TRUNCATE=56, presolve only.
#   C0  = the runner's own process-1 command (s2_solve.py --truncate 56 --split-stage build)
#   C0w = the diagnosis wrapper with window [0, 56) - its problem.lp / label vectors must be byte-identical to C0 (wrapper equivalence)
#   then ONE Gurobi call on C0 (b4_split_solve.py --probe-ordering-only); expected ITERATION_LIMIT, not INF_OR_UNBD
set -u
. "$(dirname "$0")/common.sh"
bash "$S/build.sh" C0 F1 0 56 official || { log "CONTROL_STOP:C0 build failed"; exit 2; }
bash "$S/build.sh" C0w F1 0 56 || { log "CONTROL_STOP:C0w build failed"; exit 2; }
O=$EV/CONTROL_EQUIVALENCE.txt
{
  echo "time $(now)"
  for f in split/problem.lp lp/vlabels.npy lp/clabels.npy; do
    a=$(sha256sum "$RUNROOT/C0/$f" | cut -c1-64); b=$(sha256sum "$RUNROOT/C0w/$f" | cut -c1-64)
    [ "$a" = "$b" ] && r=IDENTICAL || r=DIFFERENT
    echo "$r $f C0=$a C0w=$b"
  done
} | tee "$O"
grep -q DIFFERENT "$O" && { log "CONTROL_NOTE:wrapper output differs from the runner's TRUNCATE build (see CONTROL_EQUIVALENCE.txt)"; }
rm -f "$RUNROOT/C0w/split/problem.lp"   # the equivalence copy is not probed; its SHA256 is in CONTROL_EQUIVALENCE.txt
bash "$S/probe.sh" C0 C0; ex=$?
log "CONTROL_DONE:exit=$ex:$(now)"
echo DONE > "$RUNROOT/control.done"
