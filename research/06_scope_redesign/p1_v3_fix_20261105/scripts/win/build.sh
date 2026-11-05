#!/bin/bash
# V3 DIAG process 1 (no licence, no solver call): bash build.sh <id> <F1..F4> <start> <len> [official]
#   official: the runner's own command (s2_solve.py --truncate <len> --split-stage build; start must be 0)
#   otherwise: diag_build.py --mode build (window [start, start+len), then s2_solve.main with --truncate <len> --split-stage build)
set -u
. "$(dirname "$0")/common.sh"
ID=$1; F=$2; ST=$3; LEN=$4; HOW=${5:-window}
D=$RUNROOT/$ID
NET=$(net_of "$F"); SC=$(scen_of "$F"); CT=$(costs_of "$F")
[ -e "$D/split/SPLIT_BUILD.json" ] && { log "BUILD_SKIP:$ID:already built"; exit 0; }
mkdir -p "$D"
ARGS=(--repo "$REPO" --network "$NET" --scenario "$SC" --output "$D" --label SMOKE_TEST_ONLY --authorization "V3.1 FIX decision 195 window recheck $ID $F window [$ST,$((ST + LEN))) presolve only"
      --solver gurobi --solver-profile "$PROFILE" --scaling on --time-limit "$TL" --costs-table "$CT")
t0=$(date +%s)
log "BUILD_START:$ID:$F:[$ST,$((ST + LEN))):$HOW:$(now)"
cd "$REPO" || exit 2
if [ "$HOW" = official ]; then
  [ "$ST" = 0 ] || { log "REFUSED: official build needs start 0"; exit 2; }
  env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/s2_solve.py "${ARGS[@]}" --truncate "$LEN" --split-stage build > "$D/p1.log" 2> "$D/p1.err"; ex=$?
else
  NW=(); [ "$HOW" = native ] && NW=(--native-weights)   # diagnostic variant: weights as stored (3 h), the full-year path of s2_solve.main on the window
  env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" "$S/diag_build.py" --mode build --window-start "$ST" --window-len "$LEN" ${NW[@]+"${NW[@]}"} -- "${ARGS[@]}" > "$D/p1.log" 2> "$D/p1.err"; ex=$?
fi
el=$(( $(date +%s) - t0 ))
lpb=$(stat -c %s "$D/split/problem.lp" 2>/dev/null || echo 0)
lpsha=$( [ -f "$D/split/problem.lp" ] && sha256sum "$D/split/problem.lp" | cut -c1-64 )
dsz=$(du -sb "$D" 2>/dev/null | cut -f1)
log "BUILD_END:$ID:exit=$ex:${el}s:peak_gib=$(peak_gib "$D/p1.err"):lp_bytes=$lpb:dir_bytes=$dsz:lp_sha256=$lpsha:$(now)"
mkdir -p "$EV/runs/$ID"
for f in SOLVE_RECEIPT.json DIAG_WINDOW.json split/SPLIT_BUILD.json lp/MATH_PROBLEM.json; do [ -f "$D/$f" ] && cp "$D/$f" "$EV/runs/$ID/$(basename "$f")"; done
grep -A 25 "Command being timed" "$D/p1.err" | grep -viE "$SCRUB" > "$EV/runs/$ID/p1_time.txt" 2>/dev/null
tail -5 "$D/p1.log" | grep -viE "$SCRUB" > "$EV/runs/$ID/p1_tail.txt"
[ $ex = 0 ] || { grep -viE "$SCRUB" "$D/p1.err" | tail -40 > "$EV/runs/$ID/p1_err_tail.txt"; }
exit $ex
