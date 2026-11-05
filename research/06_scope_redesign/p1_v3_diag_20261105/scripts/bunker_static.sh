#!/bin/bash
. /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_diag_20261105/scripts/common.sh
cd "$REPO/scripts_project" || exit 2
env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" "$S/bunker_static.py" "$EV/BUNKER_STATIC_F1_F4.json" "$(net_of F1)" "$(net_of F2)" "$(net_of F3)" "$(net_of F4)" 2> "$RUNROOT/bunker_static.err"; ex=$?
log "BUNKER_STATIC:exit=$ex:peak_gib=$(peak_gib "$RUNROOT/bunker_static.err")"
[ $ex = 0 ] || tail -20 "$RUNROOT/bunker_static.err"
