#!/bin/bash
# V3 DIAG step 2: F1 calendar-month windows (evidence/F1_SNAPSHOTS.json), each: process 1 (diag_build.py, window + runner TRUNCATE path) -> process 2
# (b4_split_solve.py --probe-ordering-only, one Gurobi call). problem.lp is removed after an ITERATION_LIMIT probe (as the runner's REMOVE_LP=1);
# kept for any other status (DualReductions=0 / IIS follow-ups). Serial: never two processes at once.
#   bash months.sh [F1] [first month index 1..12] [last month index]
set -u
. "$(dirname "$0")/common.sh"
F=${1:-F1}; A=${2:-1}; Z=${3:-12}
PEAK_STOP_GIB=${PEAK_STOP_GIB:-9.5}
"$PY" -c "import json; d=json.load(open('$EV/F1_SNAPSHOTS.json'))['months']
for i,(k,v) in enumerate(sorted(d.items()),1): print(i, k, v['start'], v['length'])" > "$RUNROOT/months.txt"
while read -r i k st len; do
  [ "$i" -ge "$A" ] && [ "$i" -le "$Z" ] || continue
  id=$(printf '%s_M%02d' "$F" "$i")
  bash "$S/build.sh" "$id" "$F" "$st" "$len" || { log "MONTHS_STOP:$id:build failed"; break; }
  pk=$(peak_gib "$RUNROOT/$id/p1.err")
  if awk -v p="$pk" -v s="$PEAK_STOP_GIB" 'BEGIN {exit !(p > s)}'; then log "MONTHS_NOTE:$id:build peak ${pk} GiB > ${PEAK_STOP_GIB} GiB"; fi
  # run protection outside the profile (b4_split_solve.py --protect, recorded as protect_parameters): this machine has ~10 GiB for WSL; the control
  # (56 snapshots) used MaxMemUsed 5.96 GB in the barrier ordering after presolve. SoftMemLimit only ends a run AFTER presolve has given its verdict
  # (the log then shows "Presolved: ..." and status MEM_LIMIT instead of ITERATION_LIMIT); it never changes the presolve result.
  ex=0; [ -f "$RUNROOT/$id/split/SPLIT_SOLVE.json" ] || { bash "$S/probe.sh" "$id" "$id" --protect "SoftMemLimit=${SOFTMEM_GB:-8}"; ex=$?; }
  [ $ex = 3 ] && { log "MONTHS_STOP:$id:no token route"; break; }
  st2=$("$PY" -c "import json; print(json.load(open('$RUNROOT/$id/split/SPLIT_SOLVE.json')).get('gurobi_status_name',''))" 2>/dev/null)
  if [ "$st2" = ITERATION_LIMIT ] || { [ "$st2" = MEM_LIMIT ] && grep -q "^Presolved:" "$RUNROOT/$id/gurobi.linopy.log"; }; then rm -f "$RUNROOT/$id/split/problem.lp"; log "LP_REMOVED:$id:status ITERATION_LIMIT"; else log "LP_KEPT:$id:status=$st2"; fi
  log "DISK:$(du -sb "$RUNROOT" | cut -f1) bytes in $RUNROOT"
done < "$RUNROOT/months.txt"
log "MONTHS_DONE:$F:$A-$Z:$(now)"
echo DONE > "$RUNROOT/months_${F}_${A}_${Z}.done"
