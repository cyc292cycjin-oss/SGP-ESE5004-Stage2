#!/bin/bash
# V3 DIAG: one IIS call (iis_lp.py, gurobipy only) on a kept problem.lp. bash iis_lp.sh <build id> <iis id> [--grb K=V ...]
# IIS TimeLimit 1800 s (instruction 4); external wall clock 2,400 s on the process; MemLimit 7.5 GB (protection, recorded as an extra parameter).
set -u
. "$(dirname "$0")/common.sh"
B=$1; I=$2; shift 2
BD=$RUNROOT/$B; OD=$RUNROOT/$I
[ -f "$BD/split/problem.lp" ] || { log "IIS_REFUSED:$I:problem.lp of $B missing"; exit 2; }
[ -e "$OD" ] && { log "IIS_REFUSED:$I:folder exists"; exit 2; }
used=$(calls_used); [ "$used" -lt "$MAXCALLS" ] || { log "IIS_REFUSED:$I:Gurobi budget $used/$MAXCALLS used"; exit 2; }
r=$(gurobi_running); [ "$r" = 0 ] || { log "IIS_REFUSED:$I:$r solver processes running"; exit 2; }
token_ok || { log "IIS_REFUSED:$I:no TCP to the token server - no Gurobi call made"; exit 3; }
k=$((used + 1)); t0=$(date +%s); s0=$(now)
log "GUROBI_CALL_$k:$I:iis_lp($B $*):start:$s0"
cd "$REPO" || exit 2
mkdir -p "$RUNROOT/${I}_proc"
env GRB_LICENSE_FILE="$LICPATH" timeout -k 30 2400 /usr/bin/time -v "$PY" "$S/iis_lp.py" --build-dir "$BD" --out-dir "$OD" --time-limit 1800 --grb MemLimit=7.5 "$@" \
  > "$RUNROOT/${I}_proc/iis.log" 2> "$RUNROOT/${I}_proc/iis.err"; ex=$?
J=$OD/IIS_LP.json
jg() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1])); v=d.get(sys.argv[2]); print('' if v is None else (len(v) if isinstance(v, list) else v))" "$J" "$1" 2>/dev/null; }
oc=$(jg outcome); is=$(jg iis_seconds); nc=$(jg iis_constraint_labels); nb=$(jg iis_bound_var_labels); mm=$(jg max_mem_used_gb)
echo "$k,$I,iis,$s0,$(now),$ex,$oc,,$is,$mm,$(peak_gib "$RUNROOT/${I}_proc/iis.err"),$B $* iis_constraints=$nc iis_bound_vars=$nb" >> "$CALLS"
log "GUROBI_CALL_$k:$I:end:exit=$ex:outcome=$oc:iis_s=$is:iis_constraints=$nc:iis_bound_vars=$nb:maxmem_gb=$mm:peak_rss_gib=$(peak_gib "$RUNROOT/${I}_proc/iis.err"):$(( $(date +%s) - t0 ))s:$(now)"
mkdir -p "$EV/runs/$I"
for f in IIS_LP.json iis.ilp; do [ -f "$OD/$f" ] && cp "$OD/$f" "$EV/runs/$I/"; done
grep -viE "$SCRUB" "$OD/gurobi.iis.log" > "$EV/runs/$I/gurobi_iis_log_scrubbed.txt" 2>/dev/null
grep -viE "$SCRUB" "$RUNROOT/${I}_proc/iis.log" > "$EV/runs/$I/iis_stdout_scrubbed.txt" 2>/dev/null
grep -A 25 "Command being timed" "$RUNROOT/${I}_proc/iis.err" | grep -viE "$SCRUB" > "$EV/runs/$I/iis_time.txt" 2>/dev/null
[ $ex = 0 ] || grep -viE "$SCRUB" "$RUNROOT/${I}_proc/iis.err" | tail -30 > "$EV/runs/$I/iis_err_tail.txt"
exit $ex
