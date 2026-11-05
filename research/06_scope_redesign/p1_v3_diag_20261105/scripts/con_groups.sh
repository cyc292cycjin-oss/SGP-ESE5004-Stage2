#!/bin/bash
# V3 DIAG: constraint-container index of a build (no solver). bash con_groups.sh <build id>
set -u
. "$(dirname "$0")/common.sh"
B=$1
cd "$REPO" || exit 2
env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" "$S/con_groups.py" --build-dir "$RUNROOT/$B" --scratch "$RUNROOT/${B}_cg_scratch" --out-json "$EV/CON_GROUPS_$B.json" > "$RUNROOT/cg_$B.log" 2> "$RUNROOT/cg_$B.err"; ex=$?
log "CON_GROUPS:$B:exit=$ex:peak_gib=$(peak_gib "$RUNROOT/cg_$B.err"):$(tail -1 "$RUNROOT/cg_$B.log" | cut -c1-300)"
[ $ex = 0 ] || grep -viE "$SCRUB" "$RUNROOT/cg_$B.err" | tail -20
