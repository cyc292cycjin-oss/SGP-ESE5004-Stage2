#!/bin/bash
# V3 DIAG step 4 static table for one package network: bash annual_rhs.sh <F1..F4>
set -u
. "$(dirname "$0")/common.sh"
F=$1
cd "$REPO/scripts_project" || exit 2
env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" "$S/annual_rhs.py" "$(net_of "$F")" "$EV/ANNUAL_RHS_$F.json" 2> "$RUNROOT/annual_rhs_$F.err"; ex=$?
log "ANNUAL_RHS:$F:exit=$ex:peak_gib=$(peak_gib "$RUNROOT/annual_rhs_$F.err"):$(now)"
[ $ex = 0 ] || tail -20 "$RUNROOT/annual_rhs_$F.err"
