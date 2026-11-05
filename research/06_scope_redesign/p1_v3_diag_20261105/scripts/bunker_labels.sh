#!/bin/bash
# V3 DIAG: bunker account labels of a build (no solver). bash bunker_labels.sh <build id>
set -u
. "$(dirname "$0")/common.sh"
B=$1
cd "$REPO" || exit 2
env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" "$S/bunker_labels.py" --build-dir "$RUNROOT/$B" --scratch "$RUNROOT/${B}_bl_scratch" --out-json "$EV/BUNKER_LABELS_$B.json" > "$RUNROOT/bl_$B.log" 2> "$RUNROOT/bl_$B.err"; ex=$?
log "BUNKER_LABELS:$B:exit=$ex:peak_gib=$(peak_gib "$RUNROOT/bl_$B.err"):$(tail -1 "$RUNROOT/bl_$B.log" | cut -c1-300)"
[ $ex = 0 ] || grep -viE "$SCRUB" "$RUNROOT/bl_$B.err" | tail -20
