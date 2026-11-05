#!/bin/bash
# V3 DIAG: lp_scan.py over the exported LP arrays (lp/) of the given run ids (no solver). bash lp_scan.sh <id> [<id> ...]
set -u
. "$(dirname "$0")/common.sh"
mkdir -p "$EV/lp_scan"
for id in "$@"; do
  env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" "$S/lp_scan.py" "$RUNROOT/$id/lp" "$EV/lp_scan/LP_SCAN_$id.json" > "$RUNROOT/lp_scan_$id.log" 2> "$RUNROOT/lp_scan_$id.err"; ex=$?
  log "LP_SCAN:$id:exit=$ex:peak_gib=$(peak_gib "$RUNROOT/lp_scan_$id.err"):$(cat "$RUNROOT/lp_scan_$id.log" | cut -c1-400)"
  [ $ex = 0 ] || tail -5 "$RUNROOT/lp_scan_$id.err"
done
