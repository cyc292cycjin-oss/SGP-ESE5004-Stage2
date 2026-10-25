#!/bin/bash
# B4P local Gurobi calls, v3 = solve.sh + a memory watchdog on every process (instruction section 1: a measurement is terminated as soon as the
# machine's memory use exceeds 90 %: MemAvailable < 10 % of MemTotal -> TERM the process group, MEMORY_RULE_KILL line) + probe modes:
#   MODE=current|split|probe  SC=  N=  PROFILE=  TAG=  TL=  PROTECT="SoftMemLimit=6"  PROBE_ITERS=0|K (probe: BarIterLimit)  PROBE_P3=0|1 (probe: run process 3 too)
# User authorisation 2026-10-26 03:15 SGT: at most 8 calls, truncated 2920x3h / existing 56x3h networks, <= 365 snapshots, <= 60 min each,
# >= 5 min apart, no retry. One call = one optimize() (counted when the Gurobi process starts: results_project/b4p/.calls_used).
set -u
WT=/home/jin/wt_b4p_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0
NETS=$MAIN/results_project/m08b/builds_s01; R=$MAIN/results_project/b4p; ST=$R/SOLVES_STATUS.txt; LIC=/home/jin/gurobi.lic
export TMPDIR=$R/tmp; mkdir -p "$R/solves" "$TMPDIR"
MODE=${MODE:?}; SC=${SC:?}; N=${N:?}; PROFILE=${PROFILE:?}; TAG=${TAG:?}; TL=${TL:-3300}; PROTECT=${PROTECT:-}; PROBE_ITERS=${PROBE_ITERS:-0}; PROBE_P3=${PROBE_P3:-0}; MEASURE=${MEASURE:-}
WALL=3600; GRACE=60; GAP=300; MAXCALLS=8; MEMFRAC=10
D=$R/solves/$TAG; NET=$NETS/$SC/${SC}_2920_3h_unsolved.nc; COSTS=$NETS/$SC/costs_active_research.csv
AUTH="B4P local measurement (user authorisation 2026-10-26 03:15 SGT: at most 8 local Gurobi calls on truncated 2920x3h / existing 56x3h networks, <= 365 snapshots, <= 60 min each, >= 5 min apart, no retry; no cloud, no upload, never the full 2920x3h): $TAG mode=$MODE N=$N profile=$PROFILE"
cd "$WT" || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> "$ST"; }
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[b]4_split_solve\.py|[g]urobi_cl' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
alive() { [ -n "$(pgrep -g "$1" 2>/dev/null)" ]; }
jget() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'): d=d.get(k) if isinstance(d, dict) else None
print('' if d is None else d)" "$1" "$2" 2>/dev/null; }
peak_of() { grep -h "Maximum resident" "$1" 2>/dev/null | awk '{printf "%.2f", $NF/1048576}'; }
wall_of() { grep -h "Elapsed (wall" "$1" 2>/dev/null | awk '{print $NF}'; }
mem_low() { awk -v f=$MEMFRAC '/MemTotal/ {t=$2} /MemAvailable/ {a=$2} END {exit !(a*100 < t*f)}' /proc/meminfo; }
watch() {   # $1 pgid $2 stage: TERM the group when MemAvailable < MEMFRAC % of MemTotal (90 % rule); KILL after GRACE
  local pg=$1 stage=$2
  while alive "$pg"; do
    if mem_low; then
      log "MEMORY_RULE_KILL_${TAG}_$stage" "mem_available_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo):rss_kb=$(ps -o rss= -g "$pg" 2>/dev/null | awk '{s+=$1} END {print s}') - WSL memory above 90 %, process group terminated"
      kill -TERM -- "-$pg" 2>/dev/null; local g=0; while alive "$pg" && [ $g -lt $GRACE ]; do sleep 1; g=$((g + 1)); done; alive "$pg" && kill -KILL -- "-$pg" 2>/dev/null; break
    fi
    sleep 3
  done
}
run_watched() {   # $1 stage $2 log $3 err $4 wall s $5 with_licence (0|1), then the command: own process group, watchdog, wall-clock kill
  local stage=$1 lg=$2 er=$3 wall=$4 lic=$5; shift 5
  if [ "$lic" = 1 ]; then ( exec setsid /usr/bin/time -v env GRB_LICENSE_FILE=$LIC "$@" > "$lg" 2> "$er" ) & else ( exec setsid env -u GRB_LICENSE_FILE /usr/bin/time -v "$@" > "$lg" 2> "$er" ) & fi
  local pid=$! t0=$(date +%s); sleep 1; local pg; pg=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  watch "$pg" "$stage" & local w=$!
  while kill -0 $pid 2>/dev/null; do
    sleep 5
    if [ $(( $(date +%s) - t0 )) -ge "$wall" ]; then
      log "KILLED_${wall}S_${TAG}_$stage"; kill -TERM -- "-$pg" 2>/dev/null; local g=0
      while alive $pg && [ $g -lt $GRACE ]; do sleep 1; g=$((g + 1)); done
      alive $pg && { kill -KILL -- "-$pg" 2>/dev/null; log "KILL9_${TAG}_$stage"; }
      break
    fi
  done
  wait $pid 2>/dev/null; local ex=$?; kill $w 2>/dev/null; wait $w 2>/dev/null; return $ex
}
[ "$(git branch --show-current)" = codex/b4-prep-20261026 ] || { log WRONG_BRANCH; exit 2; }
[ -f "$LIC" ] || { log NO_LICENCE_FILE; exit 3; }
[ -e "$D" ] && { log "REFUSED_$TAG" "folder exists (never re-solved)"; exit 2; }
used=$(cat "$R/.calls_used" 2>/dev/null || echo 0)
[ "$used" -lt $MAXCALLS ] || { log "REFUSED_$TAG" "calls_used=$used >= $MAXCALLS"; exit 2; }
[ "$(busy)" = 0 ] || { log "REFUSED_$TAG" "solver process running ($(busy))"; exit 4; }
mkdir -p "$D"; echo "$MODE $SC $N $PROFILE TL=$TL PROTECT=$PROTECT PROBE_ITERS=$PROBE_ITERS MEASURE=$MEASURE" > "$D/MODE.txt"
log "START_$TAG" "mode=$MODE:sc=$SC:N=$N:profile=$PROFILE:tl=$TL:protect=${PROTECT:-none}:measure=${MEASURE:-none}:probe_iters=$PROBE_ITERS:calls_used_before=$used:head=$(git rev-parse HEAD)"
gap_wait() { if [ -f "$R/.last_solve_end" ]; then local last; last=$(cat "$R/.last_solve_end"); while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done; log "GAP_$TAG" "$(( $(date +%s) - last ))s since the previous call ended"; fi; }
SARGS=(--repo . --network "$NET" --scenario "$SC" --output "$D" --label SMOKE_TEST_ONLY --authorization "$AUTH" --solver gurobi --solver-profile "$PROFILE" --scaling on --time-limit "$TL" --costs-table "$COSTS" --truncate "$N")
case "$MODE" in
  current)
    gap_wait; [ "$(busy)" = 0 ] || { log "REFUSED_$TAG" "solver process appeared"; exit 4; }
    echo $((used + 1)) > "$R/.calls_used"; date -u +%Y-%m-%dT%H:%M:%SZ > "$D/.call_start"; log "CALL_$TAG" "call=$((used + 1)):process=s2_solve.py (single process)"
    run_watched solve "$D/solve.log" "$D/solve.err" $WALL 1 "$PY" scripts_project/s2_solve.py "${SARGS[@]}"; ex=$?
    date +%s > "$R/.last_solve_end"; date -u +%Y-%m-%dT%H:%M:%SZ > "$D/.call_end"
    log "END_$TAG" "exit=$ex:wall=$(wall_of "$D/solve.err"):peak=$(peak_of "$D/solve.err")GiB:cond=$(jget "$D/SOLVE_RECEIPT.json" termination_condition):obj=$(jget "$D/SOLVE_RECEIPT.json" objective):post_errors=$(jget "$D/SOLVE_RECEIPT.json" post_solve_errors | cut -c1-200)";;
  split|probe)
    run_watched p1 "$D/p1.log" "$D/p1.err" 2400 0 "$PY" scripts_project/s2_solve.py "${SARGS[@]}" --split-stage build; ex1=$?
    log "P1_$TAG" "exit=$ex1:wall=$(wall_of "$D/p1.err"):peak=$(peak_of "$D/p1.err")GiB:lp_bytes=$(jget "$D/split/SPLIT_BUILD.json" problem_bytes):write_s=$(jget "$D/split/SPLIT_BUILD.json" write_seconds)"
    [ $ex1 = 0 ] && [ -f "$D/split/SPLIT_BUILD.json" ] || { log "ABORT_$TAG" "process 1 failed or terminated - no Gurobi call made"; exit 5; }
    gap_wait; [ "$(busy)" = 0 ] || { log "REFUSED_$TAG" "solver process appeared"; exit 4; }
    PARGS=(--run-dir "$D")
    if [ "$MODE" = probe ]; then if [ "$PROBE_ITERS" -gt 0 ]; then PARGS+=(--probe-iterations "$PROBE_ITERS"); else PARGS+=(--probe-ordering-only); fi; fi
    for kv in $PROTECT; do PARGS+=(--protect "$kv"); done
    for kv in ${MEASURE:-}; do PARGS+=(--measure "$kv"); done   # measurement-only profile overrides (recorded as measurement_parameters)
    echo $((used + 1)) > "$R/.calls_used"; date -u +%Y-%m-%dT%H:%M:%SZ > "$D/.call_start"; log "CALL_$TAG" "call=$((used + 1)):process=b4_split_solve.py (process 2):args=${PARGS[*]:2}"
    run_watched p2 "$D/p2.log" "$D/p2.err" $WALL 1 "$PY" scripts_project/b4_split_solve.py "${PARGS[@]}"; ex2=$?
    date +%s > "$R/.last_solve_end"; date -u +%Y-%m-%dT%H:%M:%SZ > "$D/.call_end"
    S=$D/split/SPLIT_SOLVE.json
    log "P2_$TAG" "exit=$ex2:wall=$(wall_of "$D/p2.err"):peak=$(peak_of "$D/p2.err")GiB:status=$(jget $S gurobi_status_name):cond=$(jget $S termination_condition):obj=$(jget $S objective):iters=$(jget $S bar_iter_count):runtime=$(jget $S runtime_s):work=$(jget $S work_units):maxmem=$(jget $S max_mem_used_gb)GB:fp=$(jget $S fingerprint):read_s=$(jget $S read_seconds)"
    if { [ "$MODE" = split ] || [ "$PROBE_P3" = 1 ]; } && [ $ex2 = 0 ] && [ -n "$(jget $S termination_condition)" ]; then
      run_watched p3 "$D/p3.log" "$D/p3.err" 2400 0 "$PY" scripts_project/s2_solve.py "${SARGS[@]}" --split-stage assign; ex3=$?
      log "P3_$TAG" "exit=$ex3:wall=$(wall_of "$D/p3.err"):peak=$(peak_of "$D/p3.err")GiB:cond=$(jget "$D/SOLVE_RECEIPT.json" termination_condition):obj=$(jget "$D/SOLVE_RECEIPT.json" objective):post_errors=$(jget "$D/SOLVE_RECEIPT.json" post_solve_errors | cut -c1-200)"
    fi
    log "END_$TAG" "done";;
  *) log "REFUSED_$TAG" "unknown mode $MODE"; exit 2;;
esac
echo DONE >> "$D/.done"
