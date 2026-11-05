#!/bin/bash
# V3 DIAG: one group-deletion presolve probe (one Gurobi call). bash del_probe.sh <build id> <probe id> <regex> [<regex> ...]
set -u
. "$(dirname "$0")/common.sh"
B=$1; I=$2; shift 2
BD=$RUNROOT/$B; OD=$RUNROOT/$I
[ -f "$BD/split/problem.lp" ] && [ -f "$BD/lp_groups.npz" ] || { log "DEL_REFUSED:$I:problem.lp or lp_groups.npz of $B missing"; exit 2; }
[ -e "$OD" ] && { log "DEL_REFUSED:$I:folder exists"; exit 2; }
used=$(calls_used); [ "$used" -lt "$MAXCALLS" ] || { log "DEL_REFUSED:$I:Gurobi budget $used/$MAXCALLS used"; exit 2; }
r=$(gurobi_running); [ "$r" = 0 ] || { log "DEL_REFUSED:$I:$r solver processes running"; exit 2; }
token_ok || { log "DEL_REFUSED:$I:no TCP to the token server - no Gurobi call made"; exit 3; }
DR=(); while [ $# -gt 0 ]; do case "$1" in --fix-zero|--row-rhs) DR+=("$1" "$2"); shift 2;; *) DR+=(--drop "$1"); shift;; esac; done
k=$((used + 1)); t0=$(date +%s); s0=$(now)
log "GUROBI_CALL_$k:$I:del_probe($B drop $*):start:$s0"
cd "$REPO" || exit 2
mkdir -p "$RUNROOT/${I}_proc"
env GRB_LICENSE_FILE="$LICPATH" timeout -k 30 1200 /usr/bin/time -v "$PY" "$S/del_probe.py" --build-dir "$BD" --out-dir "$OD" "${DR[@]}" --grb MemLimit=7 --grb SoftMemLimit=6 \
  > "$RUNROOT/${I}_proc/del.log" 2> "$RUNROOT/${I}_proc/del.err"; ex=$?
J=$OD/DEL_PROBE.json
jg() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1])); v=d.get(sys.argv[2]); print('' if v is None else v)" "$J" "$1" 2>/dev/null; }
v=$(jg verdict); nd=$(jg rows_dropped); rt=$(jg runtime_s)
pt=$(grep -h "^Presolve time:" "$OD/gurobi.del.log" 2>/dev/null | tail -1 | awk '{print $3}' | tr -d 's')
echo "$k,$I,del_probe,$s0,$(now),$ex,$v,$pt,$rt,,$(peak_gib "$RUNROOT/${I}_proc/del.err"),$B drop[$*] rows_dropped=$nd" >> "$CALLS"
log "GUROBI_CALL_$k:$I:end:exit=$ex:verdict=$v:rows_dropped=$nd:presolve_s=$pt:peak_rss_gib=$(peak_gib "$RUNROOT/${I}_proc/del.err"):$(( $(date +%s) - t0 ))s:$(now)"
log "VERDICT:$I:$v:drop[$*]"
mkdir -p "$EV/runs/$I"; cp "$J" "$EV/runs/$I/" 2>/dev/null
grep -viE "$SCRUB" "$OD/gurobi.del.log" > "$EV/runs/$I/gurobi_log_scrubbed.txt" 2>/dev/null
[ $ex = 0 ] || grep -viE "$SCRUB" "$RUNROOT/${I}_proc/del.err" | tail -30 > "$EV/runs/$I/del_err_tail.txt"
exit $ex
