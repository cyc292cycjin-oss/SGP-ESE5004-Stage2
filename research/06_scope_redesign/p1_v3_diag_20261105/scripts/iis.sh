#!/bin/bash
# V3 DIAG step 3: build a window in this process and run ONE Gurobi environment on its problem file: presolve (profile + BarIterLimit 0 + extra
# parameters), then - when INFEASIBLE (or INF_OR_UNBD with --iis-on-infunbd) - linopy compute_infeasibilities() / print_labels (IIS <= 30 min).
#   bash iis.sh <id> <F1..F4> <start> <len> [diag_build.py options: --grb K=V ... --iis-on-infunbd]
set -u
. "$(dirname "$0")/common.sh"
ID=$1; F=$2; ST=$3; LEN=$4; shift 4
D=$RUNROOT/$ID
[ -e "$D" ] && { log "IIS_REFUSED:$ID:folder exists"; exit 2; }
used=$(calls_used); [ "$used" -lt "$MAXCALLS" ] || { log "IIS_REFUSED:$ID:Gurobi budget $used/$MAXCALLS used"; exit 2; }
r=$(gurobi_running); [ "$r" = 0 ] || { log "IIS_REFUSED:$ID:$r solver processes running"; exit 2; }
token_ok || { log "IIS_REFUSED:$ID:no TCP to the token server - no Gurobi call made"; exit 3; }
NET=$(net_of "$F"); SC=$(scen_of "$F"); CT=$(costs_of "$F")
mkdir -p "$D"
k=$((used + 1)); t0=$(date +%s); s0=$(now)
log "GUROBI_CALL_$k:$ID:iis($F [$ST,$((ST + LEN))) BarIterLimit=0 $*):start:$s0"
cd "$REPO" || exit 2
env GRB_LICENSE_FILE="$LICPATH" /usr/bin/time -v "$PY" "$S/diag_build.py" --mode iis --window-start "$ST" --window-len "$LEN" --grb BarIterLimit=0 "$@" -- \
  --repo "$REPO" --network "$NET" --scenario "$SC" --output "$D" --label SMOKE_TEST_ONLY --authorization "V3 DIAG decision 194 $ID $F window [$ST,$((ST + LEN))) presolve + IIS" \
  --solver gurobi --solver-profile "$PROFILE" --scaling on --time-limit "$TL" --costs-table "$CT" > "$D/iis.log" 2> "$D/iis.err"; ex=$?
J=$D/DIAG_IIS.json
jg() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1])); v=d.get(sys.argv[2]); print('' if v is None else (len(v) if isinstance(v, list) else v))" "$J" "$1" 2>/dev/null; }
st=$(jg status); rt=$(jg runtime_s); mm=$(jg max_mem_used_gb); ni=$(jg iis_constraint_labels); is=$(jg iis_seconds)
pt=$(grep -h "^Presolve time:" "$D/gurobi_iis_log_scrubbed.txt" 2>/dev/null | tail -1 | awk '{print $3}' | tr -d 's')
echo "$k,$ID,iis,$s0,$(now),$ex,$st,$pt,$rt,$mm,$(peak_gib "$D/iis.err"),$* iis_constraints=$ni iis_s=$is" >> "$CALLS"
log "GUROBI_CALL_$k:$ID:end:exit=$ex:status=$st:presolve_s=$pt:runtime_s=$rt:iis_constraints=$ni:iis_s=$is:peak_rss_gib=$(peak_gib "$D/iis.err"):$(( $(date +%s) - t0 ))s:$(now)"
mkdir -p "$EV/runs/$ID"
for f in DIAG_IIS.json DIAG_WINDOW.json IIS_PRINT.txt iis.ilp SOLVE_RECEIPT.json; do [ -f "$D/$f" ] && cp "$D/$f" "$EV/runs/$ID/$f"; done   # written by this diagnosis / the model (no solver log text)
[ -f "$D/gurobi_iis_log_scrubbed.txt" ] && grep -viE "$SCRUB" "$D/gurobi_iis_log_scrubbed.txt" > "$EV/runs/$ID/gurobi_iis_log_scrubbed.txt"
grep -A 25 "Command being timed" "$D/iis.err" | grep -viE "$SCRUB" > "$EV/runs/$ID/iis_time.txt" 2>/dev/null
[ $ex = 0 ] || grep -viE "$SCRUB" "$D/iis.err" | tail -40 > "$EV/runs/$ID/iis_err_tail.txt"
exit $ex
