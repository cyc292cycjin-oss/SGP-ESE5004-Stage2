#!/bin/bash
# M10P third-batch runner (instruction sections 2-3; items 133, 138-141). Extends scripts_project/m08a_run_batch.sh (per run: violations -> C1
# -> M12 allocation and Owen dual form registered in EXPORTS.json -> GATES_V6; the batch's own C1 reference with regrade and grade_history; the
# item-138 D12 stop rule) with the S4O cloud script run_365x24h.sh (own process group per solve, wall-clock kill of the whole group, monitor,
# receipt check, scrubbed exports, licence gaps), two Gurobi sessions in parallel and resume. PREPARED ONLY: it runs on the cloud instance after
# the user has rented it and authorised the batch (separate execution instruction).
#
#   GRB_LICENSE_FILE=<licence path> PY=<env python> bash run_batch3.sh --auth "<user authorisation text>"
#   The same command again resumes in the same RUN_DIR (default runs/batch3): a solve that has ended is never repeated.
#
# Runs (RUN_PLAN.md section 2; table in scripts_project/m10_batch3_summary.py RUNS; 365x24h; A = formal_barrier (Threads 8), T16 =
# formal_barrier_1e6_t16 (Threads 16)):
#   R1 integrated A | R2 disconnected A | R3 integrated T16 | R4 disconnected T16 | R5 / R6 / R7 integrated minus VN / TH / LA A |
#   R8 disconnected b1 (intra-ASEAN CO2 transport forbidden) A | R9 disconnected keeping the cross-border stock A | R10 / R11 country WACC
#   integrated / disconnected A | P1 integrated 2920x3h probe A (build + presolve + iteration timing and peak memory; wall clock 3,600 s).
# Order: phase 0 inputs and variants (no licence) -> phase 1 [R1 | R2] -> batch reference + regrade -> phase 2 [R3 | R4] -> level-2 comparison
# -> phase 3 lanes [R5 R7 R9 R11] | [R6 R8 R10] -> batch post-processing, results pack (pre_p1) -> P1 alone -> final pack.
#
# PRE-REGISTERED RULES (RUN_PLAN.md section 3; registered before any result, not changed after results have been seen):
#   * one solve per run: no retry, no parameter change, no warm start; TimeLimit 21,600 s and wall clock 22,500 s (P1: wall clock 3,600 s,
#     TimeLimit 3,600 s, i.e. the wall clock decides); the wall-clock kill ends the whole process group (TERM, GRACE_S, KILL);
#   * at most two Gurobi sessions: two runs share the instance only when the Threads of both profiles fit the container cores, otherwise the pair
#     runs one after the other; >= 330 s from the end of a solve to the next start in the same lane, and from the latest solve end (and from the
#     start of this runner: preflight licence check, tokens of an earlier runner) to the start of every phase (WLS tokens are kept >= 5 min);
#   * after every solve (Python only, GRB_LICENSE_FILE removed): violations -> C1 (reference BATCH_REFERENCE.json once R1 and R2 have ledgers,
#     before that the default reference = provisional) -> M12 allocation (dual form main value, market form beside it, alpha interval, bunker
#     player; registered in EXPORTS.json before the acceptance) -> leave-one-out right-hand-side check (R5-R7 against R1) -> GATES_V6;
#   * BATCH_REFERENCE.json from R1 / R2; every run graded before it is regraded (grade_history kept; V6_ACCEPTANCE_PROVISIONAL.json kept;
#     the Owen dual-form acceptance regraded on the same reference -> m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json);
#   * stop: only a NOT_ACCEPTED that does not hinge on the C1 reference (C1 (a) or a G2 check failed; item 138 D12) stops the batch: no new solve
#     starts; a solve already running finishes and is post-processed; the summary and the results packs are still written;
#   * not covered by the rules -> safe stop (STOP_SAFE with the reason; nothing else starts; wait for the user): a solve found started but not
#     ended on resume, a solver process running at start, a base network or variant whose SHA256 differs from the build receipt / the local
#     dry run (EXPECTED_VARIANTS.json), a missing input, more than one other solver process at a start;
#   * P1 is a probe: no C1 / M12 / GATES_V6, its numbers only choose the fourth-batch machine.
#
# Environment: PY (python of the environment), RUN_DIR, WALL_CAP_S / GUROBI_TIME_LIMIT_S / P1_WALL_CAP_S / P1_TIME_LIMIT_S / LICENCE_GAP_S
# (registered values; any other value is refused unless ALLOW_UNREGISTERED=1 - tests and the local dry run only), GRACE_S (30), MONITOR_S (60),
# P1_MONITOR_S (10), CGROUP_ROOT (/sys/fs/cgroup), CORES (default: container cgroup quota, else nproc).
# Local dry run (instruction section 5): BUILD_ONLY=1 = every run once with s2_solve.py --stop-before-solve (LP built and exported, parameters
# fixed, no solver call, GRB_LICENSE_FILE points to a non-existent file), one lane, no gaps, BUILD_CHECK.json per run, P1 parameters only.
# POST_ONLY=1: no solve at all (licence tripwire as above, no phase 0) - the post-processing of every ended run, batch reference and regrade,
# level-2, batch post-processing, summary and packs; e.g. to redo the post-processing on the instance, or the local dry run on smoke results.
# Test hooks: SOLVE_CMD, VA_CMD, C1_CMD, M12_CMD, M12A_CMD, VAR_CMD, G6_CMD, SUM_CMD, PACK_CMD, TRUNCATE (smoke tests only), DRY=1 (commands only).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
AUTH=""
while [ $# -gt 0 ]; do
  case "$1" in
    --auth) AUTH="$2"; shift 2;;
    *) echo "unknown argument $1"; exit 2;;
  esac
done
REPO=${REPO:-$HERE/repo}; NETS=${NETS:-$HERE/networks}; OUT=${RUN_DIR:-$HERE/runs/batch3}; PY=${PY:-python}
BUILD_ONLY=${BUILD_ONLY:-0}; DRY=${DRY:-0}; POST_ONLY=${POST_ONLY:-0}; TRUNCATE=${TRUNCATE:-}
NOSOLVE=0; { [ "$BUILD_ONLY" = 1 ] || [ "$DRY" = 1 ] || [ "$POST_ONLY" = 1 ]; } && NOSOLVE=1   # no Gurobi session: no licence, no gaps, one lane
R_WALL=22500; R_TL=21600; R_P1_WALL=3600; R_P1_TL=3600; R_GAP=330     # registered values (RUN_PLAN.md section 3)
WALL_CAP_S=${WALL_CAP_S:-$R_WALL}; GUROBI_TIME_LIMIT_S=${GUROBI_TIME_LIMIT_S:-$R_TL}; P1_WALL_CAP_S=${P1_WALL_CAP_S:-$R_P1_WALL}; P1_TIME_LIMIT_S=${P1_TIME_LIMIT_S:-$R_P1_TL}
LICENCE_GAP_S=${LICENCE_GAP_S:-$R_GAP}; GRACE_S=${GRACE_S:-30}; MONITOR_S=${MONITOR_S:-60}; P1_MONITOR_S=${P1_MONITOR_S:-10}; CGROUP_ROOT=${CGROUP_ROOT:-/sys/fs/cgroup}
SOLVE_CMD=${SOLVE_CMD:-"$PY $REPO/scripts_project/s2_solve.py"}; VA_CMD=${VA_CMD:-"$PY $REPO/scripts_project/l23_violation_analysis.py"}
C1_CMD=${C1_CMD:-"$PY $REPO/scripts_project/s4o_c1_precision.py"}; M12_CMD=${M12_CMD:-"$PY $REPO/scripts_project/m12_allocation.py"}
M12A_CMD=${M12A_CMD:-"$PY $REPO/scripts_project/m12_rhs_audit.py"}; VAR_CMD=${VAR_CMD:-"$PY $REPO/scripts_project/m08a_variants.py"}
G6_CMD=${G6_CMD:-"$PY $REPO/scripts_project/v5/gates_v6.py"}; SUM_CMD=${SUM_CMD:-"$PY $REPO/scripts_project/m10_batch3_summary.py"}; PACK_CMD=${PACK_CMD:-"bash $HERE/pack_results.sh"}
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'   # licence-line filter (written so that this file holds no licence keyword)
TRUNC=(); [ -n "$TRUNCATE" ] && TRUNC=(--truncate "$TRUNCATE")

if [ "${ALLOW_UNREGISTERED:-0}" != 1 ]; then
  for pair in "WALL_CAP_S:$WALL_CAP_S:$R_WALL" "GUROBI_TIME_LIMIT_S:$GUROBI_TIME_LIMIT_S:$R_TL" "P1_WALL_CAP_S:$P1_WALL_CAP_S:$R_P1_WALL" "P1_TIME_LIMIT_S:$P1_TIME_LIMIT_S:$R_P1_TL" "LICENCE_GAP_S:$LICENCE_GAP_S:$R_GAP"; do
    IFS=: read -r k v r <<< "$pair"; [ "$v" = "$r" ] || { echo "REFUSED: $k=$v differs from the registered value $r (RUN_PLAN.md section 3)"; exit 2; }
  done
  [ -z "$TRUNCATE" ] || { echo "REFUSED: TRUNCATE is for smoke tests only"; exit 2; }
fi
if [ "$NOSOLVE" = 1 ]; then
  LIC=/nonexistent/m10p_dry_run_no_licence   # tripwire: any Gurobi environment would fail
  [ -n "$AUTH" ] || AUTH="M10P no-solve mode (build-only / post-only / dry)"
else
  : "${GRB_LICENSE_FILE:?set GRB_LICENSE_FILE to the licence path provided by the user}"
  [ -r "$GRB_LICENSE_FILE" ] || { echo "GRB_LICENSE_FILE is not readable"; exit 2; }
  LIC=$GRB_LICENSE_FILE
  [ -n "$AUTH" ] || { echo "REFUSED: --auth \"<user authorisation text>\" is required"; exit 2; }
fi
command -v setsid >/dev/null 2>&1 && [ -x /usr/bin/time ] || { echo "REFUSED: setsid (util-linux) and GNU time at /usr/bin/time are required"; exit 2; }
mkdir -p "$OUT" "$OUT/export" || { echo "cannot create $OUT"; exit 2; }
ST="$OUT/STATUS.txt"; EXP="$OUT/export"; T_START=$(date +%s)
export PYTHONHASHSEED=0

now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$*" >> "$ST"; }
halted() { [ -f "$OUT/STOP" ] || [ -f "$OUT/STOP_SAFE" ]; }
safe_stop() { echo "$1" >> "$OUT/STOP_SAFE"; log "STOP_SAFE:$1:$(now) - nothing else starts; waiting for the user"; }
jget() {   # $1 json file, $2 dotted key -> value ("" when missing)
  "$PY" -c "import json,sys
d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'):
    d=d.get(k) if isinstance(d, dict) else None
print('' if d is None else d)" "$1" "$2" 2>/dev/null
}
busy() { ps -eo cmd | grep -cE '[s]2_solve.py'; }

# ---- run table (single source: scripts_project/m10_batch3_summary.py RUNS)
declare -A SC BASE SET PROF COSTS
while IFS='|' read -r rid sc base set prof costs; do
  [ -n "$rid" ] || continue; SC[$rid]=$sc; BASE[$rid]=$base; SET[$rid]=$set; PROF[$rid]=$prof; COSTS[$rid]=$costs
done < <(cd "$REPO" && $SUM_CMD runtable)
[ "${#SC[@]}" = 12 ] || { echo "REFUSED: run table not readable from $REPO (got ${#SC[@]} runs)"; exit 2; }
threads_of() { "$PY" - "$REPO" "$1" <<'P' 2>/dev/null || echo 0
import sys, yaml
from pathlib import Path
print(int(yaml.safe_load((Path(sys.argv[1]) / "configs/research/baseline.yaml").read_text())["research"]["solver"]["profiles"][sys.argv[2]].get("Threads", 0)))
P
}
declare -A THREADS
for p in formal_barrier formal_barrier_1e6_t16; do THREADS[$p]=$(threads_of $p); [ "${THREADS[$p]}" -gt 0 ] 2>/dev/null || { echo "REFUSED: Threads of profile $p not readable"; exit 2; }; done
detect_cores() {
  if [ -n "${CORES:-}" ]; then echo "$CORES"; return; fi
  local q p
  if [ -r "$CGROUP_ROOT/cpu.max" ]; then
    read -r q p < "$CGROUP_ROOT/cpu.max"
    if [ "$q" != max ] && [ "${p:-0}" -gt 0 ] 2>/dev/null; then echo $(( q / p )); return; fi
  elif [ -r "$CGROUP_ROOT/cpu/cpu.cfs_quota_us" ] && [ -r "$CGROUP_ROOT/cpu/cpu.cfs_period_us" ]; then
    q=$(cat "$CGROUP_ROOT/cpu/cpu.cfs_quota_us"); p=$(cat "$CGROUP_ROOT/cpu/cpu.cfs_period_us")
    if [ "$q" -gt 0 ] 2>/dev/null && [ "$p" -gt 0 ] 2>/dev/null; then echo $(( q / p )); return; fi
  fi
  nproc
}
NCORES=$(detect_cores)
fits() { [ $(( ${THREADS[${PROF[$1]}]} + ${THREADS[${PROF[$2]}]} )) -le "$NCORES" ]; }   # two sessions side by side only within the cores

log "START:$(now):commit=$(cat "$HERE/COMMIT" 2>/dev/null || echo none):repo_commit=$(cat "$REPO/.package_commit" 2>/dev/null || echo none):build_only=$BUILD_ONLY:post_only=$POST_ONLY:dry=$DRY:cores=$NCORES:threads_A=${THREADS[formal_barrier]}:threads_T16=${THREADS[formal_barrier_1e6_t16]}:time_limit_s=$GUROBI_TIME_LIMIT_S:wall_cap_s=$WALL_CAP_S:p1_wall_cap_s=$P1_WALL_CAP_S:p1_time_limit_s=$P1_TIME_LIMIT_S:licence_gap_s=$LICENCE_GAP_S:truncate=${TRUNCATE:-none}:resume=$([ -f "$OUT/.created" ] && echo yes || echo no)"
[ -f "$OUT/.created" ] || now > "$OUT/.created"

# ---- container cgroup memory (monitor)
cg_mem_limit_b() { local v=""
  if [ -r "$CGROUP_ROOT/memory.max" ]; then v=$(cat "$CGROUP_ROOT/memory.max"); elif [ -r "$CGROUP_ROOT/memory/memory.limit_in_bytes" ]; then v=$(cat "$CGROUP_ROOT/memory/memory.limit_in_bytes"); fi
  case "$v" in ""|max) echo "";; *) [ "${#v}" -ge 19 ] && echo "" || echo "$v";; esac; }
cg_mem_used_b() { if [ -r "$CGROUP_ROOT/memory.current" ]; then cat "$CGROUP_ROOT/memory.current"; elif [ -r "$CGROUP_ROOT/memory/memory.usage_in_bytes" ]; then cat "$CGROUP_ROOT/memory/memory.usage_in_bytes"; else echo ""; fi; }
group_pids() { pgrep -g "$1" 2>/dev/null; }
group_alive() { [ -n "$(group_pids "$1")" ]; }
monitor() {   # $1 pgid $2 rid $3 solve dir $4 interval s
  local pg=$1 f="$OUT/MONITOR_$2.csv" t0 lim; t0=$(date +%s); lim=$(cg_mem_limit_b)
  echo "utc,elapsed_s,rss_gib_group,cgroup_mem_used_gib,cgroup_mem_limit_gib,host_mem_available_gib,disk_free_gib,gurobi_last_line" > "$f"
  while group_alive "$pg"; do
    local rss=0 p r used avail disk last
    for p in $(group_pids "$pg"); do r=$(ps -o rss= -p "$p" 2>/dev/null | tr -d ' '); [ -n "$r" ] && rss=$((rss + r)); done
    used=$(cg_mem_used_b); avail=$(awk '/MemAvailable/ {printf "%.2f", $2/1048576}' /proc/meminfo 2>/dev/null); disk=$(df -Pk "$OUT" | awk 'NR==2 {printf "%.1f", $4/1048576}')
    last=$(tail -n 1 "$3/gurobi.linopy.log" 2>/dev/null | grep -viE "$SCRUB" | tr ',' ';' | cut -c1-160)
    echo "$(now),$(( $(date +%s) - t0 )),$(awk -v k=$rss 'BEGIN {printf "%.2f", k/1048576}'),$([ -n "$used" ] && awk -v b="$used" 'BEGIN {printf "%.2f", b/1073741824}'),$([ -n "$lim" ] && awk -v b="$lim" 'BEGIN {printf "%.2f", b/1073741824}'),$avail,$disk,$last" >> "$f"
    sleep "$4"
  done
}
receipt_state() {   # -> post_solve | pre_solve | stopped_before_solve | missing | unreadable
  [ -f "$1" ] || { echo missing; return; }
  "$PY" - "$1" <<'P' 2>/dev/null || echo unreadable
import json, sys
r = json.load(open(sys.argv[1]))
print("stopped_before_solve" if r.get("stop_before_solve") else ("post_solve" if ("termination_condition" in r and "finished_epoch" in r) else "pre_solve"))
P
}
c1_summary() {   # PRECISION.json -> "<grade>:accepted=<bool>:abc=<a><b><c>:ref=<batch|default>"
  "$PY" - "$1" <<'P' 2>/dev/null || echo unreadable
import json, sys
r = json.load(open(sys.argv[1])); g = r.get("grade", {}); a = r.get("acceptance", {}); src = str((r.get("reference") or {}).get("source", ""))
print(f"{g.get('grade')}:accepted={a.get('accepted')}:abc={int(bool(g.get('a')))}{int(bool(g.get('b')))}{int(bool(g.get('c')))}:ref={'batch' if src.startswith('this batch') else 'default'}")
P
}
ref_independent() {   # V6_ACCEPTANCE.json -> 1 when NOT_ACCEPTED does not hinge on the C1 reference (C1 (a) or a G2 check failed; unreadable -> 1)
  "$PY" -c "import json,sys; a=json.load(open(sys.argv[1])); print(int((not a['G1']['a']) or not all(a['G2'][k]['passed'] for k in ('G2_1', 'G2_2', 'G2_3'))))" "$1" 2>/dev/null || echo 1
}

# ---- networks of the runs
base_net() { echo "$NETS/${BASE[$1]}_unsolved.nc"; }
base_scen() { echo "${BASE[$1]%%_*}"; }
net_of() {   # base network or the variant generated in phase 0
  if [ -z "${SET[$1]}" ]; then base_net "$1"; else ls "$OUT/variants/$1"/*_unsolved.nc 2>/dev/null | head -1; fi
}
registered_of() {   # GATES_V6 G2.1 registered SHA256: variant receipt output.sha256; base: build receipt (daily network for an untruncated 365x24h run)
  if [ -n "${SET[$1]}" ]; then jget "$(ls "$OUT/variants/$1"/*_VARIANT_RECEIPT.json 2>/dev/null | head -1)" output.sha256
  elif [ "${BASE[$1]##*_}" = 24h ] && [ -z "$TRUNCATE" ]; then jget "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" daily_network.sha256
  else jget "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" network.sha256; fi
}

# ---- phase 0: inputs, base networks against the build receipts, variants against the local dry run
prepare() {
  local f rid
  [ "$POST_ONLY" = 1 ] && { log "PREPARE:skipped (POST_ONLY: no solve, no variants needed)"; return 0; }
  for f in integrated_365_24h_unsolved.nc disconnected_365_24h_unsolved.nc integrated_2920_3h_unsolved.nc integrated_BUILD_RECEIPT.json disconnected_BUILD_RECEIPT.json \
           integrated_costs_active_research.csv disconnected_costs_active_research.csv; do
    [ -s "$NETS/$f" ] || { safe_stop "MISSING_INPUT:networks/$f"; return 1; }
  done
  [ "$DRY" = 1 ] || [ "$(busy)" = 0 ] || { safe_stop "SOLVER_PROCESS_RUNNING_AT_START:$(busy) s2_solve processes (an earlier runner?)"; return 1; }
  local bc; bc=$(cd "$REPO" && $SUM_CMD base-check --nets "$NETS" --out "$OUT/BASE_CHECK.json" 2>> "$OUT/prepare.err")
  log "BASE_CHECK:$bc"; [ "$bc" = all_equal ] || { safe_stop "BASE_NETWORK_SHA256:$bc"; return 1; }
  mkdir -p "$OUT/variants"
  for rid in R5 R6 R7 R8 R9 R10 R11; do
    local V="$OUT/variants/$rid" costs=()
    if [ ! -f "$(ls "$V"/*_VARIANT_RECEIPT.json 2>/dev/null | head -1)" ]; then
      mkdir -p "$V"; [ "${SET[$rid]%%=*}" = finance.wacc_mode ] && costs=(--costs "$NETS/${COSTS[$rid]}_costs_active_research.csv")
      ( cd "$REPO" && env -u GRB_LICENSE_FILE PYTHONHASHSEED=0 $VAR_CMD --repo "$REPO" --base "$(base_net "$rid")" --out "$V" --set "${SET[$rid]}" ${costs[@]+"${costs[@]}"} > "$V/variant.log" 2>&1 )
      log "VARIANT_$rid:generated:exit=$?:set=${SET[$rid]}"
    fi
    if [ -f "$HERE/EXPECTED_VARIANTS.json" ]; then
      local vc; vc=$(cd "$REPO" && $SUM_CMD variants-check --variants "$OUT/variants" --expected "$HERE/EXPECTED_VARIANTS.json" --rid "$rid" 2>> "$OUT/prepare.err"); local rc=$?
      log "VARIANT_$rid:$vc"; [ $rc = 0 ] || { safe_stop "VARIANT_SHA256_$rid:$vc"; return 1; }
    else
      safe_stop "EXPECTED_VARIANTS.json missing in the package (variants cannot be compared with the local dry run)"; return 1
    fi
  done
  return 0
}

# ---- one solve, never repeated
wait_gap() {   # $1 epoch of the previous solve end (empty = none), $2 tag
  [ "$NOSOLVE" = 1 ] || [ -z "$1" ] && return 0
  while [ $(( $(date +%s) - $1 )) -lt "$LICENCE_GAP_S" ]; do sleep 5; done
  log "GAP_$2:$(( $(date +%s) - $1 ))s:$(now)"
}
phase_gap() {   # >= LICENCE_GAP_S after the latest solve end of any run and after the start of this runner
  local last=$T_START m f
  for f in "$OUT"/*/.solve_end; do [ -f "$f" ] || continue; m=$(cat "$f"); [ "$m" -gt "$last" ] && last=$m; done
  wait_gap "$last" "PHASE_$1"
}
write_run_json() {   # $1 rid $2 network $3 time limit $4 wall cap $5 label
  local d="$OUT/$1"
  "$PY" - "$d/RUN.json" "$1" "${SC[$1]}" "${BASE[$1]}" "${SET[$1]}" "${PROF[$1]}" "$NETS/${COSTS[$1]}_costs_active_research.csv" "$2" "$(sha256sum "$2" | cut -c1-64)" \
        "$(registered_of "$1")" "$3" "$4" "$5" "${TRUNCATE:-}" "$d" "$EXP/$1" "${THREADS[${PROF[$1]}]}" "$BUILD_ONLY" "$AUTH" <<'P'
import json, sys, time
k = ["rid", "scenario", "base", "set", "profile", "costs_table", "network", "network_sha256", "registered_sha256", "time_limit", "wall_cap_s", "label", "truncate",
     "output", "export", "threads", "build_only", "authorization"]
d = dict(zip(k, sys.argv[2:]))
d.update(time_limit=float(d["time_limit"]), wall_cap_s=int(d["wall_cap_s"]), threads=int(d["threads"]), build_only=d["build_only"] == "1",
         truncate=(int(d["truncate"]) if d["truncate"] else None), written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
json.dump(d, open(sys.argv[1], "w"), indent=1)
P
}
solve_run() {   # $1 rid, $2 .solve_end file of the previous run in the lane (may be empty); returns 1 when the lane must stop
  local rid=$1 d="$OUT/$1"; mkdir -p "$d"
  if [ -f "$d/.ended" ]; then log "SKIP_ENDED_$rid:$(cat "$d/.cond" 2>/dev/null) (ended before; never re-solved)"; return 0; fi
  if [ "$POST_ONLY" = 1 ]; then log "POST_ONLY_$rid:not solved - nothing to post-process"; return 0; fi
  if [ -f "$d/.started" ]; then safe_stop "INTERRUPTED_$rid:started $(cat "$d/.started") but never ended - not repeated (rule: no retry); user decision"; return 1; fi
  local net; net=$(net_of "$rid"); [ -n "$net" ] && [ -s "$net" ] || { safe_stop "MISSING_NETWORK_$rid:${net:-variant missing}"; return 1; }
  local tl=$GUROBI_TIME_LIMIT_S wall=$WALL_CAP_S label=BATCH3_365X24H mon=$MONITOR_S
  [ "$rid" = P1 ] && { tl=$P1_TIME_LIMIT_S; wall=$P1_WALL_CAP_S; label=BATCH3_P1_PROBE_2920X3H; mon=$P1_MONITOR_S; }
  [ -n "$TRUNCATE" ] && label=SMOKE_TEST_ONLY
  local cmd=($SOLVE_CMD --repo "$REPO" --network "$net" --scenario "${SC[$rid]}" --output "$d" --label "$label" --authorization "$AUTH; run $rid"
             --solver gurobi --solver-profile "${PROF[$rid]}" --scaling on --time-limit "$tl" --costs-table "$NETS/${COSTS[$rid]}_costs_active_research.csv" ${TRUNC[@]+"${TRUNC[@]}"})
  [ "$BUILD_ONLY" = 1 ] && cmd+=(--stop-before-solve)
  write_run_json "$rid" "$net" "$tl" "$wall" "$label"
  if [ "$DRY" = 1 ] || { [ "$BUILD_ONLY" = 1 ] && [ "$rid" = P1 ]; }; then log "DRY-RUN_$rid:${cmd[*]}"; return 0; fi
  if [ -n "${2:-}" ] && [ -f "$2" ]; then wait_gap "$(cat "$2")" "$rid"; fi
  halted && { log "NOT_STARTED_$rid:batch halted during the gap"; return 1; }
  [ "$(busy)" -lt 2 ] || { safe_stop "SOLVER_BUSY_$rid:$(busy) s2_solve processes running (at most one other session)"; return 1; }
  now > "$d/.started"
  ( cd "$REPO" && exec setsid /usr/bin/time -v env GRB_LICENSE_FILE="$LIC" "${cmd[@]}" > "$d/solve.log" 2> "$d/solve.err" ) &
  local pid=$! start; start=$(date +%s); sleep 1
  local pg; pg=$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  echo "$(now) pid=$pid pgid=$pg" > "$d/.started"
  log "SOLVE_$rid:pid=$pid:pgid=$pg:profile=${PROF[$rid]}:threads=${THREADS[${PROF[$rid]}]}:time_limit=$tl:wall_cap=$wall:network_sha256=$(jget "$d/RUN.json" network_sha256):$(now)"
  monitor "$pg" "$rid" "$d" "$mon" & local m=$! killed=0
  while kill -0 "$pid" 2>/dev/null; do
    sleep 5
    if [ $(( $(date +%s) - start )) -ge "$wall" ]; then
      log "KILLED_${wall}S_$rid:$(now):group=$pg:members=$(group_pids "$pg" | tr '\n' ' ')"; kill -TERM -- "-$pg" 2>/dev/null; killed=1
      local g=0; while group_alive "$pg" && [ $g -lt "$GRACE_S" ]; do sleep 1; g=$((g + 1)); done
      group_alive "$pg" && { kill -KILL -- "-$pg" 2>/dev/null; log "KILL9_$rid:$(now):after_grace_${GRACE_S}s"; }
      break
    fi
  done
  wait "$pid" 2>/dev/null; local ex=$?
  local w=0; while group_alive "$pg" && [ $w -lt 120 ]; do sleep 1; w=$((w + 1)); done
  group_alive "$pg" && { kill -KILL -- "-$pg" 2>/dev/null; sleep 1; log "GROUP_SURVIVED_$rid:killed_after_120s"; }
  kill "$m" 2>/dev/null; wait "$m" 2>/dev/null
  date +%s > "$d/.solve_end"
  local rs cond; rs=$(receipt_state "$d/SOLVE_RECEIPT.json")
  if [ "$rs" = post_solve ]; then cond=$(jget "$d/SOLVE_RECEIPT.json" termination_condition); [ -n "$cond" ] || cond=none
  elif [ "$rs" = stopped_before_solve ]; then cond=stopped_before_solve
  elif [ $killed = 1 ]; then cond=killed_pre_solve
  else cond=none; fi
  echo "$cond" > "$d/.cond"; echo "$ex" > "$d/.exit"; now > "$d/.ended"
  log "RUN_$rid:$cond:exit=$ex:receipt=$rs:$(( $(date +%s) - start ))s:peak=$(grep -h 'Maximum resident' "$d/solve.err" 2>/dev/null | awk '{printf "%.2fGiB", $NF/1048576}')"
  return 0
}

# ---- post-processing of one run (instruction section 3.4); idempotent: every step skips an output that exists
accept() {   # $1 rid -> label (V6_ACCEPTANCE.json)
  local d="$OUT/$1" reg
  if [ -n "${SET[$1]}" ]; then reg=(--registered-sha256 "$(jget "$d/RUN.json" registered_sha256)"); else reg=(--build-receipt "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json"); fi
  local lab; lab=$(cd "$REPO" && env -u GRB_LICENSE_FILE $G6_CMD accept --solve-dir "$d" "${reg[@]}" --repo "$REPO" 2>> "$d/v6.err" | tail -1)
  echo "$lab" > "$d/.label"; echo "$lab"
}
stop_check() {   # $1 rid: item 138 D12
  local d="$OUT/$1" lab; lab=$(cat "$d/.label" 2>/dev/null)
  [ "$lab" = NOT_ACCEPTED ] || return 0
  if [ "$(ref_independent "$d/V6_ACCEPTANCE.json")" = 1 ]; then
    grep -qx "$1" "$OUT/STOP" 2>/dev/null || echo "$1" >> "$OUT/STOP"
    log "STOP_NOT_ACCEPTED:$1:$(now) - C1 (a) or G2 failed (item 138 D12): no new solve starts; no retry, no parameter change; user decision"
  else
    log "NOT_ACCEPTED_REFERENCE_DEPENDENT:$1:$(c1_summary "$d/PRECISION.json") - C1 (b) / (c) only: no stop (item 138 D12)"
  fi
}
export_run() {   # $1 rid -> export/<rid>/ (scrubbed logs; no LP / solution arrays, no raw solver log)
  local d="$OUT/$1" e="$EXP/$1" f; mkdir -p "$e"
  for f in RUN.json SOLVE_RECEIPT.json V5_GATES.json INTERIOR_CHECKS.json BUNKER_ACCOUNT.json GUROBI_LOG_SCRUBBED.txt RESOURCE.jsonl CO2_FLOWS.json GAP_TABLE.json \
           EMISSIONS_BY_COUNTRY.json CAPACITY_BY_TECH_COUNTRY.json cross_border_flows.csv COUNTRY_COST_LEDGER.csv COUNTRY_COST_LEDGER_USD2020.csv COUNTRY_COST_LEDGER_DETAIL.csv \
           LEDGER_IDENTITY.json NODAL_PRICES.csv DUALS_BY_CONSTRAINT.nc DUALS_INDEX.csv COMPONENT_COST_BREAKDOWN.csv COMPONENT_COST_BREAKDOWN_SUMMARY.json costs_active_research.csv \
           PRECISION.json PRECISION.md VIOLATIONS.json C1_ERR_TAIL.txt EXPORTS.json ALLOCATION.json ALLOCATION.csv ALLOCATION.md ALLOCATION_LINES.csv \
           V6_ACCEPTANCE.json V6_ACCEPTANCE_PROVISIONAL.json BUILD_CHECK.json; do
    [ -f "$d/$f" ] && cp "$d/$f" "$e/"
  done
  for f in m12_owen m12_loo_rhs; do [ -d "$d/$f" ] && { mkdir -p "$e/$f"; cp "$d/$f"/*.json "$d/$f"/*.csv "$d/$f"/*.md "$e/$f/" 2>/dev/null; }; done
  [ -f "$d/solve.log" ] && grep -viE "$SCRUB" "$d/solve.log" > "$e/solve_log_scrubbed.txt"
  [ -f "$d/lp/MATH_PROBLEM.json" ] && cp "$d/lp/MATH_PROBLEM.json" "$e/"
  [ -f "$d/v5/kkt_summary.json" ] && cp "$d/v5/kkt_summary.json" "$e/"
  ls "$d"/*_solved.nc > /dev/null 2>&1 && cp "$d"/*_solved.nc "$e/"
  [ -f "$OUT/MONITOR_$1.csv" ] && cp "$OUT/MONITOR_$1.csv" "$e/"
  grep -A 30 "Command being timed" "$d/solve.err" > "$e/solve_time.txt" 2>/dev/null
  [ -d "$OUT/variants/$1" ] && { mkdir -p "$EXP/variants/$1"; cp "$OUT/variants/$1"/*.json "$OUT/variants/$1"/variant.log "$EXP/variants/$1/" 2>/dev/null; }
  local c; c=$(cat "$d/.cond" 2>/dev/null)
  if [ -n "$c" ] && [ "$c" != optimal ] && [ "$c" != stopped_before_solve ]; then
    tail -60 "$d/gurobi.linopy.log" 2>/dev/null | grep -viE "$SCRUB" > "$e/LOG_TAIL_NONOPTIMAL.txt"; tail -60 "$d/solve.err" 2>/dev/null | grep -viE "$SCRUB" > "$e/STDERR_TAIL_NONOPTIMAL.txt"
  fi
}
post_run() {   # $1 rid
  local rid=$1 d="$OUT/$1"
  [ "$DRY" = 1 ] && return 0
  [ -f "$d/RUN.json" ] || return 0
  if [ "$BUILD_ONLY" = 1 ]; then
    if [ "$rid" = P1 ]; then local pc; pc=$(cd "$REPO" && $SUM_CMD param-check --dir "$d" --repo "$REPO" 2>> "$d/build_check.err"); log "PARAM_CHECK_P1:$pc"
    else local bc; bc=$(cd "$REPO" && $SUM_CMD build-check --dir "$d" --repo "$REPO" 2>> "$d/build_check.err"); log "BUILD_CHECK_$rid:$bc"; fi
    export_run "$rid"; return 0
  fi
  [ "$rid" = P1 ] && { p1_post; return 0; }
  [ -f "$d/.ended" ] || return 0
  local net sc lab ref=(); net=$(jget "$d/RUN.json" network); sc=$(jget "$d/RUN.json" scenario); lab=$(jget "$d/RUN.json" label)
  [ -f "$OUT/BATCH_REFERENCE.json" ] && ref=(--reference "$OUT/BATCH_REFERENCE.json")
  if [ -f "$d/solution/X.npy" ] && [ ! -f "$d/VIOLATIONS.json" ]; then
    ( cd "$REPO" && exec env -u GRB_LICENSE_FILE /usr/bin/time -v $VA_CMD --repo "$REPO" --solve-dir "$d" --network "$net" --scenario "$sc" --label "$lab" --out "$d/VIOLATIONS.json" \
        ${TRUNC[@]+"${TRUNC[@]}"} > "$d/c1_violations.log" 2> "$d/c1_violations.err" ); log "VIOLATIONS_$rid:exit=$?"
  fi
  if [ ! -f "$d/PRECISION.json" ]; then
    ( cd "$REPO" && exec env -u GRB_LICENSE_FILE /usr/bin/time -v $C1_CMD run --repo "$REPO" --solve-dir "$d" --network "$net" --scenario "$sc" --label "$lab" --violations "$d/VIOLATIONS.json" \
        ${ref[@]+"${ref[@]}"} ${TRUNC[@]+"${TRUNC[@]}"} > "$d/c1_precision.log" 2> "$d/c1_precision.err" ); local rc=$?
    [ $rc = 0 ] || grep -viE "$SCRUB" "$d/c1_precision.err" | tail -40 > "$d/C1_ERR_TAIL.txt"
    log "C1_$rid:exit=$rc:$( [ -f "$d/PRECISION.json" ] && c1_summary "$d/PRECISION.json" || echo missing):$( [ ${#ref[@]} -gt 0 ] && echo final || echo provisional)"
  fi
  if [ -f "$d/SOLVE_RECEIPT.json" ] && [ ! -f "$d/ALLOCATION.json" ]; then
    ( cd "$REPO" && exec env -u GRB_LICENSE_FILE PYTHONHASHSEED=0 $M12_CMD run --repo "$REPO" --solve-dir "$d" --scenario "$sc" --label "BATCH3_$rid" --out "$d" --register \
        > "$d/m12.log" 2> "$d/m12.err" ); log "M12_$rid:exit=$?"
  fi
  if [ -f "$d/solution/X.npy" ] && [ -f "$d/ALLOCATION.json" ] && [ ! -f "$d/m12_owen/OWEN.json" ]; then
    ( cd "$REPO" && exec env -u GRB_LICENSE_FILE PYTHONHASHSEED=0 /usr/bin/time -v $M12A_CMD audit --repo "$REPO" --network "$net" --scenario "$sc" --solve-dir "$d" --allocation "$d/ALLOCATION.json" \
        --tag "BATCH3_$rid" --out "$d/m12_owen" --register-dir "$d" ${TRUNC[@]+"${TRUNC[@]}"} > "$d/m12_owen.log" 2> "$d/m12_owen.err" ); log "M12_OWEN_$rid:exit=$?"
  fi
  case "$rid" in R5|R6|R7)
    if [ -f "$OUT/R1/m12_owen/RHS_BY_FAMILY_OWNER.csv" ] && [ -f "$d/m12_owen/RHS_BY_FAMILY_OWNER.csv" ] && [ ! -f "$d/m12_loo_rhs/LOO_RHS_CHECK.json" ]; then
      local cc; cc=$(echo "${SET[$rid]}" | sed -E 's/.*\[([A-Z]+)\].*/\1/')
      ( cd "$REPO" && exec env -u GRB_LICENSE_FILE $M12A_CMD loo --full "$OUT/R1/m12_owen/RHS_BY_FAMILY_OWNER.csv" --variant "$d/m12_owen/RHS_BY_FAMILY_OWNER.csv" --removed "$cc" \
          --out "$d/m12_loo_rhs" > "$d/m12_loo_rhs.log" 2>&1 ); log "RHS_CHECK_$rid:exit=$?:$(tail -1 "$d/m12_loo_rhs.log" 2>/dev/null)"
    fi;;
  esac
  log "V6_$rid:$(accept "$rid"):$( [ -f "$d/PRECISION.json" ] && c1_summary "$d/PRECISION.json" | sed 's/.*:ref=/ref=/')"
  export_run "$rid"; stop_check "$rid"
}

# ---- batch reference and regrade (after phase 1; repeated after every phase: idempotent)
regrade_all() {
  [ "$DRY" = 1 ] || [ "$BUILD_ONLY" = 1 ] && return 0
  if [ ! -f "$OUT/BATCH_REFERENCE.json" ]; then
    if [ -f "$OUT/R1/COUNTRY_COST_LEDGER.csv" ] && [ -f "$OUT/R2/COUNTRY_COST_LEDGER.csv" ]; then
      ( cd "$REPO" && env -u GRB_LICENSE_FILE $C1_CMD reference --integrated "$OUT/R1" --disconnected "$OUT/R2" --out "$OUT/BATCH_REFERENCE.json" > "$OUT/batch_reference.log" 2>&1 )
      log "BATCH_REFERENCE:exit=$?:$(now):R1=$(cat "$OUT/R1/.cond" 2>/dev/null):R2=$(cat "$OUT/R2/.cond" 2>/dev/null)"
    else
      log "BATCH_REFERENCE:not_available:R1/R2 ledgers missing - the runs keep the provisional default reference"; return 0
    fi
  fi
  [ -f "$OUT/BATCH_REFERENCE.json" ] || return 0
  local d rid
  for d in "$OUT"/R*/; do
    d=${d%/}; rid=${d##*/}; [ -f "$d/PRECISION.json" ] || continue
    c1_summary "$d/PRECISION.json" | grep -q ':ref=batch$' && continue
    [ -f "$d/V6_ACCEPTANCE.json" ] && cp "$d/V6_ACCEPTANCE.json" "$d/V6_ACCEPTANCE_PROVISIONAL.json"
    ( cd "$REPO" && env -u GRB_LICENSE_FILE $C1_CMD regrade --solve-dir "$d" --reference "$OUT/BATCH_REFERENCE.json" > "$d/c1_regrade.log" 2>&1 ); local rc=$?
    if [ -f "$d/m12_owen/OWEN.json" ]; then
      ( cd "$REPO" && env -u GRB_LICENSE_FILE $M12A_CMD regrade --owen "$d/m12_owen/OWEN.json" --precision "$d/PRECISION.json" --out "$d/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json" \
          > "$d/m12_owen_regrade.log" 2>&1 )
    fi
    log "REGRADE_$rid:exit=$rc:$(c1_summary "$d/PRECISION.json"):provisional=$(cat "$d/.label" 2>/dev/null):final=$(accept "$rid")"
    export_run "$rid"; stop_check "$rid"
  done
}

# ---- lanes and phases
lane() {   # $1 lane name, then rids one after the other (>= LICENCE_GAP_S after the previous solve of the lane)
  local name=$1 prev="" rid; shift
  for rid in "$@"; do
    halted && { log "LANE_$name:$rid not started (batch halted)"; break; }
    solve_run "$rid" "${prev:+$OUT/$prev/.solve_end}" || break
    post_run "$rid"; prev=$rid
  done
}
pair_phase() {   # $1 phase name, $2 $3 rids
  halted && return 0
  phase_gap "$1"; halted && return 0
  if [ "$NOSOLVE" != 1 ] && fits "$2" "$3"; then
    log "PHASE_$1:parallel:$2+$3:threads=$(( ${THREADS[${PROF[$2]}]} + ${THREADS[${PROF[$3]}]} )):cores=$NCORES:$(now)"
    lane A "$2" & local a=$!; sleep 2; lane B "$3" & local b=$!; wait $a; wait $b
  else
    log "PHASE_$1:one_after_the_other:$2,$3:threads=$(( ${THREADS[${PROF[$2]}]} + ${THREADS[${PROF[$3]}]} )):cores=$NCORES$( [ "$NOSOLVE" = 1 ] && echo ':no_solve_mode'):$(now)"
    lane A "$2" "$3"
  fi
}
lanes_phase() {   # phase 3: two lanes when two profile-A sessions fit the cores
  halted && return 0
  phase_gap 3; halted && return 0
  if [ "$NOSOLVE" != 1 ] && fits R5 R6; then
    log "PHASE_3:two_lanes:A=R5,R7,R9,R11:B=R6,R8,R10:cores=$NCORES:$(now)"
    lane A R5 R7 R9 R11 & local a=$!; sleep 2; lane B R6 R8 R10 & local b=$!; wait $a; wait $b
  else
    log "PHASE_3:one_lane:R5..R11:cores=$NCORES$( [ "$NOSOLVE" = 1 ] && echo ':no_solve_mode'):$(now)"
    lane A R5 R6 R7 R8 R9 R10 R11
  fi
}
level2_step() {
  [ "$DRY" = 1 ] || [ "$BUILD_ONLY" = 1 ] && return 0
  ( cd "$REPO" && $SUM_CMD level2 --out-dir "$OUT" > "$OUT/level2.log" 2>&1 )
  ( cd "$REPO" && $G6_CMD select-profile --level2 "$OUT/LEVEL2.json" --repo "$REPO" > "$OUT/PROFILE_CHOICE.json" 2> "$OUT/select_profile.err" )
  log "PROFILE_CHOICE:$(jget "$OUT/PROFILE_CHOICE.json" profile):$(jget "$OUT/PROFILE_CHOICE.json" reason)"
}
batch_post() {   # instruction section 3.5: leave-one-out check, B6 / benefit and proportional rules, sensitivity differences, level-2 comparison, summary
  # $1 = summary: only the summary and the batch export (after P1)
  if [ "$BUILD_ONLY" != 1 ] && [ "$DRY" != 1 ] && [ "${1:-}" != summary ]; then
    local args=() rid
    for rid in R5 R6 R7; do [ -f "$OUT/$rid/SOLVE_RECEIPT.json" ] && args+=(--loo "$(echo "${SET[$rid]}" | sed -E 's/.*\[([A-Z]+)\].*/\1/')=$OUT/$rid"); done
    if [ ${#args[@]} -gt 0 ] && [ -f "$OUT/R1/SOLVE_RECEIPT.json" ]; then
      ( cd "$REPO" && env -u GRB_LICENSE_FILE $M12_CMD loo --full "$OUT/R1" "${args[@]}" --standalone "$OUT/R2" --out "$OUT/M12_LOO" > "$OUT/M12_LOO.log" 2>&1 )
      log "M12_LOO:exit=$?:runs=$(( ${#args[@]} / 2 )):$(tail -1 "$OUT/M12_LOO.log" 2>/dev/null)"
    else log "M12_LOO:not_computable:no leave-one-out or no R1 result"; fi
    local lc=(); [ -f "$OUT/M12_LOO/LOO_CHECK.json" ] && lc=(--loo-check "$OUT/M12_LOO/LOO_CHECK.json")
    if [ -f "$OUT/R1/ALLOCATION.json" ] && [ -f "$OUT/R2/ALLOCATION.json" ]; then
      ( cd "$REPO" && env -u GRB_LICENSE_FILE $M12_CMD benefit --repo "$REPO" --integrated "$OUT/R1" --disconnected "$OUT/R2" --out "$OUT/M12_BENEFIT" ${lc[@]+"${lc[@]}"} > "$OUT/M12_BENEFIT.log" 2>&1 )
      log "M12_BENEFIT:exit=$?:loo_check=$([ ${#lc[@]} -gt 0 ] && echo yes || echo no):$(tail -1 "$OUT/M12_BENEFIT.log" 2>/dev/null)"
    else log "M12_BENEFIT:not_computable:R1 / R2 allocations missing"; fi
    level2_step
  fi
  ( cd "$REPO" && $SUM_CMD summary --out-dir "$OUT" > "$OUT/summary.log" 2>&1 ); log "SUMMARY:exit=$?:$(tail -1 "$OUT/summary.log" | cut -c1-300)"
  mkdir -p "$EXP/batch"
  for f in STATUS.txt BASE_CHECK.json BATCH_REFERENCE.json LEVEL2.json PROFILE_CHOICE.json BATCH3_SUMMARY.json BATCH3_SUMMARY.md STOP STOP_SAFE; do [ -f "$OUT/$f" ] && cp "$OUT/$f" "$EXP/batch/"; done
  for f in M12_LOO M12_BENEFIT; do [ -d "$OUT/$f" ] && { mkdir -p "$EXP/batch/$f"; cp -r "$OUT/$f"/. "$EXP/batch/$f/"; }; done
}
p1_post() {
  local d="$OUT/P1" e="$EXP/P1" f; mkdir -p "$e"
  [ -f "$d/gurobi.linopy.log" ] && grep -viE "$SCRUB" "$d/gurobi.linopy.log" > "$e/P1_GUROBI_LOG_SCRUBBED.txt"
  for f in RUN.json SOLVE_RECEIPT.json RESOURCE.jsonl; do [ -f "$d/$f" ] && cp "$d/$f" "$e/"; done
  [ -f "$OUT/MONITOR_P1.csv" ] && cp "$OUT/MONITOR_P1.csv" "$e/"
  grep -A 30 "Command being timed" "$d/solve.err" > "$e/solve_time.txt" 2>/dev/null
  tail -60 "$d/solve.err" 2>/dev/null | grep -viE "$SCRUB" > "$e/STDERR_TAIL.txt"
  ( cd "$REPO" && $SUM_CMD p1 --dir "$d" --log "$e/P1_GUROBI_LOG_SCRUBBED.txt" --out "$e/P1_SUMMARY.json" > "$d/p1_summary.log" 2>&1 ); log "P1_SUMMARY:exit=$?:$(tail -1 "$d/p1_summary.log" | cut -c1-300)"
}
pack() {   # $1 tag
  [ "$DRY" = 1 ] && return 0
  cp "$ST" "$EXP/batch/" 2>/dev/null
  local r; r=$($PACK_CMD "$OUT" "$1" 2>&1 | tail -1); log "PACK_$1:$r"
}

# ---- the batch
prepare || { log "HALTED:$(now):phase 0"; batch_post summary; pack halted_phase0; exit 3; }
pair_phase 1 R1 R2
regrade_all
pair_phase 2 R3 R4
regrade_all
level2_step
lanes_phase
regrade_all
batch_post
pack pre_p1
if ! halted; then
  phase_gap P1
  halted || { solve_run P1 "" && post_run P1; }
fi
batch_post summary
if halted; then
  pack halted
  log "HALTED:$(now):$(cat "$OUT/STOP" "$OUT/STOP_SAFE" 2>/dev/null | tr '\n' ' ')- waiting for the user (no retry, no parameter change)"
  exit 3
fi
pack final
log "DONE:$(now)"
exit 0
