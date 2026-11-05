#!/bin/bash
# V3 DIAG process 2 = the runner's b4_split_solve.py, presolve only (--probe-ordering-only: BarIterLimit 0, every other parameter from the profile).
#   bash probe.sh <build id> <probe id> [--measure KEY=VALUE ...]
#   probe id = build id: the build folder itself; otherwise a new folder whose SPLIT_BUILD.json / SOLVE_RECEIPT.json are copies and lp/ links to the build
#   (b4_split_solve.py never repeats a folder). One Gurobi call, counted before it starts.
set -u
. "$(dirname "$0")/common.sh"
B=$1; P=$2; shift 2
# SoftMemLimit capped at PROBE_SOFTMEM_CAP GB (default 6): F1_M04 passed presolve and then reached MaxMemUsed 14.2 GB (RSS 10.16 GiB, swap) in the
# ordering under SoftMemLimit 8; presolve itself needed <= 5.13 GB in the failing months (F1_M01). Protection only, recorded as protect_parameters.
A2=(); for x in "$@"; do case "$x" in SoftMemLimit=*) v=${x#SoftMemLimit=}; c=${PROBE_SOFTMEM_CAP:-6}; awk -v v="$v" -v c="$c" 'BEGIN {exit !(v > c)}' && x="SoftMemLimit=$c";; esac; A2+=("$x"); done
set -- ${A2[@]+"${A2[@]}"}
BD=$RUNROOT/$B; PD=$RUNROOT/$P
[ -f "$BD/split/SPLIT_BUILD.json" ] || { log "PROBE_REFUSED:$P:no build $B"; exit 2; }
[ -f "$BD/split/problem.lp" ] || { log "PROBE_REFUSED:$P:problem.lp of $B removed"; exit 2; }
if [ "$P" != "$B" ]; then
  [ -e "$PD" ] && { log "PROBE_REFUSED:$P:folder exists"; exit 2; }
  mkdir -p "$PD/split"; cp "$BD/split/SPLIT_BUILD.json" "$PD/split/"; cp "$BD/SOLVE_RECEIPT.json" "$PD/"; ln -s "$BD/lp" "$PD/lp"
  [ -f "$BD/DIAG_WINDOW.json" ] && cp "$BD/DIAG_WINDOW.json" "$PD/"
fi
[ -f "$PD/split/SPLIT_SOLVE.json" ] && { log "PROBE_REFUSED:$P:already probed"; exit 2; }
used=$(calls_used); [ "$used" -lt "$MAXCALLS" ] || { log "PROBE_REFUSED:$P:Gurobi budget $used/$MAXCALLS used"; exit 2; }
r=$(gurobi_running); [ "$r" = 0 ] || { log "PROBE_REFUSED:$P:$r solver processes running"; exit 2; }
token_ok || { log "PROBE_REFUSED:$P:no TCP to the token server (AnyConnect?) - no Gurobi call made"; exit 3; }
k=$((used + 1)); t0=$(date +%s); s0=$(now)
log "GUROBI_CALL_$k:$P:probe(b4_split_solve --probe-ordering-only $*):start:$s0"
cd "$REPO" || exit 2
env GRB_LICENSE_FILE="$LICPATH" /usr/bin/time -v "$PY" scripts_project/b4_split_solve.py --run-dir "$PD" --probe-ordering-only "$@" > "$PD/p2.log" 2> "$PD/p2.err"; ex=$?
J=$PD/split/SPLIT_SOLVE.json
jg() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1])); v=d.get(sys.argv[2]); print('' if v is None else v)" "$J" "$1" 2>/dev/null; }
st=$(jg gurobi_status_name); rt=$(jg runtime_s); mm=$(jg max_mem_used_gb)
pt=$(grep -h "^Presolve time:" "$PD/gurobi.linopy.log" 2>/dev/null | tail -1 | awk '{print $3}' | tr -d 's')
pr=$(grep -h "^Presolve removed" "$PD/gurobi.linopy.log" 2>/dev/null | tail -1 | tr ',' ';' | cut -c1-120)
echo "$k,$P,probe,$s0,$(now),$ex,$st,$pt,$rt,$mm,$(peak_gib "$PD/p2.err"),$* $pr" >> "$CALLS"
log "GUROBI_CALL_$k:$P:end:exit=$ex:status=$st:presolve_s=$pt:runtime_s=$rt:maxmem_gb=$mm:peak_rss_gib=$(peak_gib "$PD/p2.err"):$(( $(date +%s) - t0 ))s:$(now)"
mkdir -p "$EV/runs/$P"
cp "$J" "$EV/runs/$P/" 2>/dev/null
grep -viE "$SCRUB" "$PD/gurobi.linopy.log" > "$EV/runs/$P/gurobi_log_scrubbed.txt" 2>/dev/null
grep -A 25 "Command being timed" "$PD/p2.err" | grep -viE "$SCRUB" > "$EV/runs/$P/p2_time.txt" 2>/dev/null
grep -viE "$SCRUB" "$PD/p2.log" > "$EV/runs/$P/p2_log_scrubbed.txt" 2>/dev/null
exit $ex
