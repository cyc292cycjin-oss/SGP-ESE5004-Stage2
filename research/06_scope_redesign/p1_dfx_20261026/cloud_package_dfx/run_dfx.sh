#!/bin/bash
# DFX 365x24h screening runner (RUN_PLAN_DFX.md; DFX instruction v3 F6.2): the third-batch runner run_batch3.sh (M10P / M10A / M10R: per run
# violations -> C1 -> M12 allocation + Owen dual form -> GATES_V6; the batch's own C1 reference from the two reference runs with regrade and
# grade_history; graded stop rule; own process group per solve with a wall-clock kill, monitor, receipt check, scrubbed exports, licence gaps,
# two lanes, resume) with the DFX run table: V1 integrated / V2 disconnected on the v2 365x24h networks (demand fix F1-F4, commit 72083fde),
# profile formal_barrier_1e6_t16 (Threads 16). PREPARED ONLY: it runs on the AutoDL instance after the user has authorised phase 4.
#
#   GRB_LICENSE_FILE=<licence path> PY=<env python> bash run_dfx.sh --auth "<user authorisation text>"
#   The same command again resumes in the same RUN_DIR (default runs/dfx): a solve that has ended is never repeated.
#
# Runs (RUN_PLAN_DFX.md section 2; single source scripts_project/dfx_batch.py RUNS / SCHEDULE / TIME_LIMIT_S): V1 integrated T16 | V2 disconnected
# T16, one phase [V1] | [V2]. No variant, no leave-one-out, no level-2 comparison (LOO is left to the 2920x3h formal runs).
#
# PRE-REGISTERED RULES (RUN_PLAN_DFX.md section 3; registered before any v2 solve, not changed after results have been seen):
#   * one solve per run: no retry, no parameter change, no warm start; TimeLimit V1 21,600 s / V2 10,800 s (user amendment 2026-10-27, registered
#     before any v2 365x24h solve; first registration 3 x the third-batch R3 / R4 wall clock = 14,646 / 4,269 s) and wall-clock cap = TimeLimit +
#     1,200 s per run (dfx_batch.py limits: single source); the wall-clock kill ends the whole process group (TERM, GRACE_S, KILL);
#   * at most two Gurobi sessions: V1 and V2 side by side only when the container has >= 33 cores (2 x Threads 16 + 1 core for post-processing),
#     otherwise one lane V1 -> V2; >= 330 s from the end of a solve to the next start in the lane, and from the latest solve end (and from the start
#     of this runner: preflight licence check, tokens of an earlier runner) to the start of the phase (WLS tokens are kept >= 5 min);
#   * after every solve (Python only, GRB_LICENSE_FILE removed): violations -> C1 (reference BATCH_REFERENCE.json once V1 and V2 have ledgers,
#     before that the default reference = provisional) -> M12 allocation (dual form main value, market form beside it, alpha interval, bunker
#     player; registered in EXPORTS.json before the acceptance) -> Owen dual-form audit -> GATES_V6 (--build-receipt: the daily 365x24h network
#     SHA256 is the registered value of an untruncated run) -> graded class (dfx_batch.py stop-class);
#   * BATCH_REFERENCE.json from V1 / V2; every run graded before it is regraded (grade_history kept; V6_ACCEPTANCE_PROVISIONAL.json kept; the Owen
#     dual-form acceptance regraded on the same reference -> m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json);
#   * graded stop rule (RUN_PLAN_DFX 3.3): any run with a G2 check failed (structure or input; without a returned solution only the checks that
#     need no solution) stops the batch; V1 or V2 - both are batch reference runs - without a returned solution or with C1 (a) failed stops the
#     batch; C1 (b) / (c) alone never stops. Stop: no new solve starts; a solve already running finishes and is post-processed; the summary and
#     the results packs are written; the user decides;
#   * not covered by the rules -> safe stop (STOP_SAFE with the reason; nothing else starts; wait for the user): a solve found started but not
#     ended on resume, a solver process running at start, a base network whose SHA256 differs from the build receipt or the registered value,
#     a 2920x3h file in the package, a missing input, more than one other solver process at a start;
#   * batch post-processing (RUN_PLAN_DFX 3.4): B6 = V2 - V1 (gate_b6_cost), M12 benefit (V1 / V2 allocations), DFX_SUMMARY.json / .md with the
#     comparison against the third-batch R3 / R4 (same profile, optimal; main reference) and R1 / R2 (alongside) and the registered first-order
#     prediction (BATCH3_REFERENCE_VALUES.json of the package; description only, never an acceptance criterion), scrubbed exports, light / full packs.
#
# Environment: PY (python of the environment), RUN_DIR, LICENCE_GAP_S (registered 330), GUROBI_TIME_LIMIT_S / WALL_CAP_S (override of EVERY run;
# refused unless ALLOW_UNREGISTERED=1 - tests and the local dry run only), GRACE_S (30), MONITOR_S (60), CGROUP_ROOT (/sys/fs/cgroup),
# CORES (default: container cgroup quota, else nproc), POST_TIMEOUT_S (1800), PACK_TIMEOUT_S (7200). TMPDIR = <run dir>/tmp (data disk).
# Local dry run (instruction F6.3): BUILD_ONLY=1 = every run once with s2_solve.py --stop-before-solve (LP built and exported, parameters fixed,
# no solver call, GRB_LICENSE_FILE points to a non-existent file), one lane, no gaps, BUILD_CHECK.json per run. POST_ONLY=1: no solve at all
# (licence tripwire as above, no phase 0) - the post-processing of every ended run, batch reference and regrade, batch post-processing, summary
# and packs. Test hooks: SOLVE_CMD, VA_CMD, C1_CMD, M12_CMD, M12A_CMD, G6_CMD, SUM_CMD, PACK_CMD, TRUNCATE (smoke tests only), DRY=1 (commands only).
# A formal run (solve mode without ALLOW_UNREGISTERED) refuses every test hook; the no-solve modes refuse --auth (M10A B5.5).
# M10A inheritance: busy() counts the python s2_solve.py processes only (the GNU time wrapper line also holds "s2_solve.py"); every post-processing
# / batch step runs under timeout with a thread budget (container cores minus the Threads of the solves running now); a failed or timed-out step
# is POSTPROC_ERROR and never changes the schedule; the violation analysis and C1 are redone ONCE after a failure (M10A supplement 01 D2).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
AUTH=""
while [ $# -gt 0 ]; do
  case "$1" in
    --auth) AUTH="$2"; shift 2;;
    *) echo "unknown argument $1 (run_dfx.sh takes --auth only; no --only / --repost / --summary-s1 modes)"; exit 2;;
  esac
done
REPO=${REPO:-$HERE/repo}; NETS=${NETS:-$HERE/networks}; OUT=${RUN_DIR:-$HERE/runs/dfx}; PY=${PY:-python}
BUILD_ONLY=${BUILD_ONLY:-0}; DRY=${DRY:-0}; POST_ONLY=${POST_ONLY:-0}; TRUNCATE=${TRUNCATE:-}
NOSOLVE=0; { [ "$BUILD_ONLY" = 1 ] || [ "$DRY" = 1 ] || [ "$POST_ONLY" = 1 ]; } && NOSOLVE=1   # no Gurobi session: no licence, no gaps, one lane
R_GAP=330; R_PAR_CORES=33     # registered values (RUN_PLAN_DFX.md 3.2); the per-run TimeLimit / wall cap come from dfx_batch.py limits
LICENCE_GAP_S=${LICENCE_GAP_S:-$R_GAP}; GRACE_S=${GRACE_S:-30}; MONITOR_S=${MONITOR_S:-60}; CGROUP_ROOT=${CGROUP_ROOT:-/sys/fs/cgroup}
# M10A (B5.5): test hooks present in the environment, recorded before the defaults below fill them in; FORMAL = solve mode without ALLOW_UNREGISTERED
HOOKS_SET=$(for k in SOLVE_CMD VA_CMD C1_CMD M12_CMD M12A_CMD G6_CMD SUM_CMD PACK_CMD TRUNCATE $(compgen -A variable | grep -E '^FAKE_'); do [ -z "${!k:-}" ] || printf '%s,' "$k"; done)
FORMAL=0; [ "$NOSOLVE" = 0 ] && [ "${ALLOW_UNREGISTERED:-0}" != 1 ] && FORMAL=1
SOLVE_CMD=${SOLVE_CMD:-"$PY $REPO/scripts_project/s2_solve.py"}; VA_CMD=${VA_CMD:-"$PY $REPO/scripts_project/l23_violation_analysis.py"}
C1_CMD=${C1_CMD:-"$PY $REPO/scripts_project/s4o_c1_precision.py"}; M12_CMD=${M12_CMD:-"$PY $REPO/scripts_project/m12_allocation.py"}
M12A_CMD=${M12A_CMD:-"$PY $REPO/scripts_project/m12_rhs_audit.py"}; G6_CMD=${G6_CMD:-"$PY $REPO/scripts_project/v5/gates_v6.py"}
SUM_CMD=${SUM_CMD:-"$PY $REPO/scripts_project/dfx_batch.py"}; PACK_CMD=${PACK_CMD:-"bash $HERE/pack_results.sh"}
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'   # licence-line filter (written so that this file holds no licence keyword)
TRUNC=(); [ -n "$TRUNCATE" ] && TRUNC=(--truncate "$TRUNCATE")

if [ "${ALLOW_UNREGISTERED:-0}" != 1 ]; then
  [ "$LICENCE_GAP_S" = "$R_GAP" ] || { echo "REFUSED: LICENCE_GAP_S=$LICENCE_GAP_S differs from the registered value $R_GAP (RUN_PLAN_DFX.md 3.2)"; exit 2; }
  for k in GUROBI_TIME_LIMIT_S WALL_CAP_S; do [ -z "${!k:-}" ] || { echo "REFUSED: $k is set - the TimeLimit / wall cap of every run are the registered values of dfx_batch.py (RUN_PLAN_DFX.md 3.1); overrides only with ALLOW_UNREGISTERED=1 (tests, local dry run)"; exit 2; }; done
  [ -z "$TRUNCATE" ] || { echo "REFUSED: TRUNCATE is for smoke tests only"; exit 2; }
fi
if [ "$FORMAL" = 1 ] && [ -n "$HOOKS_SET" ]; then   # M10A (B5.5): a stand-in or smoke switch left in the shell would run the batch without the solver
  echo "REFUSED: ${HOOKS_SET%,} set - test hooks are not allowed in a formal run (unset them; ALLOW_UNREGISTERED=1 is for tests and the local dry run only)"; exit 2
fi
if [ "$NOSOLVE" = 1 ] && [ -n "$AUTH" ]; then   # M10A (B5.5): BUILD_ONLY / POST_ONLY / DRY left in the shell would turn the authorised run into a no-solve run
  echo "REFUSED: --auth together with BUILD_ONLY / POST_ONLY / DRY - the no-solve modes take no authorisation text; unset them for the formal run"; exit 2
fi
if [ "$NOSOLVE" = 1 ]; then
  LIC=/nonexistent/dfx_dry_run_no_licence   # tripwire: any Gurobi environment would fail
  [ -n "$AUTH" ] || AUTH="DFX no-solve mode (build-only / post-only / dry)"
else
  : "${GRB_LICENSE_FILE:?set GRB_LICENSE_FILE to the licence path provided by the user}"
  [ -r "$GRB_LICENSE_FILE" ] || { echo "GRB_LICENSE_FILE is not readable"; exit 2; }
  LIC=$GRB_LICENSE_FILE
  [ -n "$AUTH" ] || { echo "REFUSED: --auth \"<user authorisation text>\" is required"; exit 2; }
fi
command -v setsid >/dev/null 2>&1 && command -v timeout >/dev/null 2>&1 && [ -x /usr/bin/time ] || { echo "REFUSED: setsid (util-linux), timeout (coreutils) and GNU time at /usr/bin/time are required"; exit 2; }
mkdir -p "$OUT" "$OUT/export" "$OUT/tmp" || { echo "cannot create $OUT"; exit 2; }
ST="$OUT/STATUS.txt"; EXP="$OUT/export"; ERRF="$OUT/POSTPROC_ERRORS"
export TMPDIR="$OUT/tmp"   # M10A (B5.4): temporary files (linopy LP problem file of each solve, Python tempfile) on the data disk inside the run dir
T_START=$(date +%s)
export PYTHONHASHSEED=0
POST_TIMEOUT_S=${POST_TIMEOUT_S:-1800}; PACK_TIMEOUT_S=${PACK_TIMEOUT_S:-7200}   # M10A (B5.2): per post-processing step / per pack

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
busy() {   # running s2_solve.py python processes; M10A: the GNU time / setsid / env wrapper lines hold the same text and are not counted
  ps -eo args= | grep -E '[s]2_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '
}

# ---- run table, schedule and registered limits (single source: scripts_project/dfx_batch.py)
declare -A SC BASE SET PROF COSTS TL WALL
while IFS='|' read -r rid sc base set prof costs; do
  [ -n "$rid" ] || continue; SC[$rid]=$sc; BASE[$rid]=$base; SET[$rid]=$set; PROF[$rid]=$prof; COSTS[$rid]=$costs
done < <(cd "$REPO" && $SUM_CMD runtable)
[ "${#SC[@]}" = 2 ] || { echo "REFUSED: run table not readable from $REPO (got ${#SC[@]} runs; expected V1, V2)"; exit 2; }
for rid in "${!SET[@]}"; do [ -z "${SET[$rid]}" ] || { echo "REFUSED: run $rid has a variant set (${SET[$rid]}) - the DFX batch solves the base networks only"; exit 2; }; done
declare -A LANE_A LANE_B
while IFS='|' read -r ph la lb; do [ -n "$ph" ] && { LANE_A[$ph]=$la; LANE_B[$ph]=$lb; }; done < <(cd "$REPO" && $SUM_CMD schedule)
[ "${#LANE_A[@]}" = 1 ] || { echo "REFUSED: schedule not readable from $REPO (got ${#LANE_A[@]} phases; expected 1)"; exit 2; }
while IFS='|' read -r rid tl wall; do [ -n "$rid" ] && { TL[$rid]=$tl; WALL[$rid]=$wall; }; done < <(cd "$REPO" && $SUM_CMD limits)
[ "${#TL[@]}" = 2 ] || { echo "REFUSED: registered limits not readable from $REPO (dfx_batch.py limits)"; exit 2; }
if [ -n "${GUROBI_TIME_LIMIT_S:-}" ]; then for rid in "${!TL[@]}"; do TL[$rid]=$GUROBI_TIME_LIMIT_S; done; fi   # ALLOW_UNREGISTERED only (refused above otherwise)
if [ -n "${WALL_CAP_S:-}" ]; then for rid in "${!WALL[@]}"; do WALL[$rid]=$WALL_CAP_S; done; fi
threads_of() { "$PY" - "$REPO" "$1" <<'P' 2>/dev/null || echo 0
import sys, yaml
from pathlib import Path
print(int(yaml.safe_load((Path(sys.argv[1]) / "configs/research/baseline.yaml").read_text())["research"]["solver"]["profiles"][sys.argv[2]].get("Threads", 0)))
P
}
declare -A THREADS
for rid in "${!PROF[@]}"; do p=${PROF[$rid]}; [ -n "${THREADS[$p]:-}" ] && continue; THREADS[$p]=$(threads_of "$p"); [ "${THREADS[$p]}" -gt 0 ] 2>/dev/null || { echo "REFUSED: Threads of profile $p not readable"; exit 2; }; done
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
max_threads() { local m=0 r; for r in "$@"; do [ "${THREADS[${PROF[$r]}]}" -gt $m ] && m=${THREADS[${PROF[$r]}]}; done; echo $m; }
aux_threads() {   # M10A (B5.3): thread budget of an auxiliary Python process = container cores minus the Threads of every solve running now (>= 1)
  local used=0 d rid k
  for d in "$OUT"/V*/; do d=${d%/}; rid=${d##*/}; [ -f "$d/.started" ] && [ ! -f "$d/.ended" ] && [ -n "${PROF[$rid]:-}" ] && used=$((used + ${THREADS[${PROF[$rid]}]})); done
  k=$((NCORES - used)); [ $k -ge 1 ] || k=1; echo $k
}
aux_env() { local k; k=$(aux_threads); echo "OMP_NUM_THREADS=$k MKL_NUM_THREADS=$k OPENBLAS_NUM_THREADS=$k NUMEXPR_MAX_THREADS=$k"; }
aux() {   # an auxiliary command: in $REPO, licence removed, thread budget, timeout (TERM, KILL 30 s later; the whole process group of the step)
  ( cd "$REPO" && exec env -u GRB_LICENSE_FILE $(aux_env) timeout -k 30 "$POST_TIMEOUT_S" "$@" )
}
keep_failed() {   # M10A supplement 01 D2: $1 run dir, then file names - the incomplete outputs of a failed step are kept as <name>.failed<n> (never deleted)
  local d=$1 f n; shift
  for f in "$@"; do [ -e "$d/$f" ] || continue; n=1; while [ -e "$d/$f.failed$n" ]; do n=$((n + 1)); done; mv "$d/$f" "$d/$f.failed$n"; done
}
va_cmd() {   # $1 rid $2 run dir $3 network $4 scenario $5 label -> exit code of the violation analysis step
  step "$1" violations /usr/bin/time -v $VA_CMD --repo "$REPO" --solve-dir "$2" --network "$3" --scenario "$4" --label "$5" --out "$2/VIOLATIONS.json" \
      ${TRUNC[@]+"${TRUNC[@]}"} > "$2/c1_violations.log" 2> "$2/c1_violations.err"
}
c1_cmd() {   # $1 rid $2 run dir $3 network $4 scenario $5 label, then the reference arguments -> exit code of the C1 step
  local rid=$1 d=$2 net=$3 sc=$4 lab=$5; shift 5
  step "$rid" c1 /usr/bin/time -v $C1_CMD run --repo "$REPO" --solve-dir "$d" --network "$net" --scenario "$sc" --label "$lab" --violations "$d/VIOLATIONS.json" \
      "$@" ${TRUNC[@]+"${TRUNC[@]}"} > "$d/c1_precision.log" 2> "$d/c1_precision.err"
}
step() {   # $1 rid (or batch) $2 step name, then the command: aux + record; a non-zero exit (crash, timeout) is POSTPROC_ERROR and never changes the schedule
  local rid=$1 name=$2 rc t=$POST_TIMEOUT_S; shift 2; [ "$name" = pack ] && t=$PACK_TIMEOUT_S
  ( cd "$REPO" && exec env -u GRB_LICENSE_FILE $(aux_env) timeout -k 30 "$t" "$@" ); rc=$?
  [ $rc = 0 ] || { echo "$rid $name exit=$rc $(now)" >> "$ERRF"
    log "POSTPROC_ERROR:$rid:$name:exit=$rc$( { [ $rc = 124 ] || [ $rc = 137 ]; } && echo ":timeout_${t}s"):$(now) - recorded in POSTPROC_ERRORS; the schedule goes on (redo with POST_ONLY=1); missing C1 / GATES_V6 inputs follow the rules"; }
  return $rc
}

log "START:$(now):commit=$(cat "$HERE/COMMIT" 2>/dev/null || echo none):repo_commit=$(cat "$REPO/.package_commit" 2>/dev/null || echo none):mode=batch:build_only=$BUILD_ONLY:post_only=$POST_ONLY:dry=$DRY:cores=$NCORES:threads_T16=${THREADS[formal_barrier_1e6_t16]:-?}:time_limit_s=V1=${TL[V1]},V2=${TL[V2]}:wall_cap_s=V1=${WALL[V1]},V2=${WALL[V2]}:licence_gap_s=$LICENCE_GAP_S:parallel_min_cores=$R_PAR_CORES:schedule=1[${LANE_A[1]}|${LANE_B[1]}]:truncate=${TRUNCATE:-none}:resume=$([ -f "$OUT/.created" ] && echo yes || echo no):tmpdir=$TMPDIR:post_timeout_s=$POST_TIMEOUT_S:allow_unregistered=${ALLOW_UNREGISTERED:-0}:hooks=${HOOKS_SET%,}"
[ "$FORMAL" = 0 ] && [ "$NOSOLVE" = 0 ] && log "NOTE:ALLOW_UNREGISTERED=1 in solve mode - tests only; hooks=${HOOKS_SET%,}"
[ -f "$OUT/.created" ] || now > "$OUT/.created"

# ---- container cgroup memory (monitor)
cg_mem_limit_b() { local v=""
  if [ -r "$CGROUP_ROOT/memory.max" ]; then v=$(cat "$CGROUP_ROOT/memory.max"); elif [ -r "$CGROUP_ROOT/memory/memory.limit_in_bytes" ]; then v=$(cat "$CGROUP_ROOT/memory/memory.limit_in_bytes"); fi
  case "$v" in ""|max) echo "";; *) [ "${#v}" -ge 19 ] && echo "" || echo "$v";; esac; }
cg_mem_used_b() { if [ -r "$CGROUP_ROOT/memory.current" ]; then cat "$CGROUP_ROOT/memory.current"; elif [ -r "$CGROUP_ROOT/memory/memory.usage_in_bytes" ]; then cat "$CGROUP_ROOT/memory/memory.usage_in_bytes"; else echo ""; fi; }
cg_anon_b() { awk '$1 == "anon" {print $2}' "$CGROUP_ROOT/memory.stat" 2>/dev/null; }
group_pids() { pgrep -g "$1" 2>/dev/null; }
group_alive() { [ -n "$(group_pids "$1")" ]; }
monitor() {   # $1 pgid $2 rid $3 solve dir $4 interval s
  local pg=$1 f="$OUT/MONITOR_$2.csv" t0 lim; t0=$(date +%s); lim=$(cg_mem_limit_b)
  echo "utc,elapsed_s,rss_gib_group,cgroup_mem_used_gib,cgroup_anon_gib,cgroup_mem_limit_gib,host_mem_available_gib,disk_free_gib,gurobi_last_line" > "$f"
  while group_alive "$pg"; do
    local rss=0 p r used anon avail disk last
    for p in $(group_pids "$pg"); do r=$(ps -o rss= -p "$p" 2>/dev/null | tr -d ' '); [ -n "$r" ] && rss=$((rss + r)); done
    used=$(cg_mem_used_b); anon=$(cg_anon_b); avail=$(awk '/MemAvailable/ {printf "%.2f", $2/1048576}' /proc/meminfo 2>/dev/null); disk=$(df -Pk "$OUT" | awk 'NR==2 {printf "%.1f", $4/1048576}')
    last=$(tail -n 1 "$3/gurobi.linopy.log" 2>/dev/null | grep -viE "$SCRUB" | tr ',' ';' | cut -c1-160)
    echo "$(now),$(( $(date +%s) - t0 )),$(awk -v k=$rss 'BEGIN {printf "%.2f", k/1048576}'),$([ -n "$used" ] && awk -v b="$used" 'BEGIN {printf "%.2f", b/1073741824}'),$([ -n "$anon" ] && awk -v b="$anon" 'BEGIN {printf "%.2f", b/1073741824}'),$([ -n "$lim" ] && awk -v b="$lim" 'BEGIN {printf "%.2f", b/1073741824}'),$avail,$disk,$last" >> "$f"
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

# ---- networks of the runs (base networks only; the file given to s2_solve is always the registered 365x24h daily network)
base_net() { echo "$NETS/${BASE[$1]}_unsolved.nc"; }
base_scen() { echo "${BASE[$1]%%_*}"; }
registered_of() {   # GATES_V6 G2.1 registered SHA256 = build receipt daily_network.sha256 (the 365x24h file; RUN_PLAN_DFX section 1). A TRUNCATE run
  # (smoke tests / truncated dry run only) still solves the same daily file truncated in memory: the dry-run build check compares the file SHA256;
  # a truncated SOLVE is never accepted (gates_v6.py takes the 2920x3h SHA256 for a truncated run) and never formal.
  jget "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" daily_network.sha256
}

# ---- phase 0: inputs and the base networks against the build receipts and the registered values
prepare() {
  local f
  [ "$POST_ONLY" = 1 ] && { log "PREPARE:skipped (POST_ONLY: no solve)"; return 0; }
  for f in integrated_365_24h_unsolved.nc disconnected_365_24h_unsolved.nc integrated_BUILD_RECEIPT.json disconnected_BUILD_RECEIPT.json \
           integrated_costs_active_research.csv disconnected_costs_active_research.csv; do
    [ -s "$NETS/$f" ] || { safe_stop "MISSING_INPUT:networks/$f"; return 1; }
  done
  [ "$DRY" = 1 ] || [ "$(busy)" = 0 ] || { safe_stop "SOLVER_PROCESS_RUNNING_AT_START:$(busy) s2_solve processes (an earlier runner?)"; return 1; }
  local reg=(); [ "${ALLOW_UNREGISTERED:-0}" = 1 ] && reg=(--no-registered)   # stand-in tests on synthetic files: receipt checks only
  local bc; bc=$(aux $SUM_CMD base-check --nets "$NETS" --out "$OUT/BASE_CHECK.json" ${reg[@]+"${reg[@]}"} 2>> "$OUT/prepare.err")
  log "BASE_CHECK:$bc$( [ ${#reg[@]} -gt 0 ] && echo ":receipts_only(ALLOW_UNREGISTERED)")"; [ "$bc" = all_equal ] || { safe_stop "BASE_NETWORK_SHA256:$bc"; return 1; }
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
  if [ -f "$d/.started" ]; then safe_stop "INTERRUPTED_$rid:started $(cat "$d/.started") but never ended - not repeated (rule: no retry); a resource restart is a new RUN_DIR with the user's authorisation"; return 1; fi
  local net; net=$(base_net "$rid"); [ -s "$net" ] || { safe_stop "MISSING_NETWORK_$rid:$net"; return 1; }
  local tl=${TL[$rid]} wall=${WALL[$rid]} label=DFX_365X24H mon=$MONITOR_S
  [ -n "$TRUNCATE" ] && label=SMOKE_TEST_ONLY
  local cmd=($SOLVE_CMD --repo "$REPO" --network "$net" --scenario "${SC[$rid]}" --output "$d" --label "$label" --authorization "$AUTH; run $rid"
             --solver gurobi --solver-profile "${PROF[$rid]}" --scaling on --time-limit "$tl" --costs-table "$NETS/${COSTS[$rid]}_costs_active_research.csv" ${TRUNC[@]+"${TRUNC[@]}"})
  [ "$BUILD_ONLY" = 1 ] && cmd+=(--stop-before-solve)
  write_run_json "$rid" "$net" "$tl" "$wall" "$label"
  if [ "$DRY" = 1 ]; then log "DRY-RUN_$rid:${cmd[*]}"; return 0; fi
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

# ---- post-processing of one run; idempotent: every step skips an output that exists
accept() {   # $1 rid -> label (V6_ACCEPTANCE.json); the registered SHA256 comes from the build receipt (daily network for the untruncated 365x24h run)
  local d="$OUT/$1" lab; lab=$(aux $G6_CMD accept --solve-dir "$d" --build-receipt "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" --repo "$REPO" 2>> "$d/v6.err" | tail -1)
  echo "$lab" > "$d/.label"; echo "$lab"
}
stop_check() {   # $1 rid: graded stop rule (RUN_PLAN_DFX 3.3; both runs are batch reference runs)
  local d="$OUT/$1" lab cls act; lab=$(cat "$d/.label" 2>/dev/null)
  case "$lab" in ACCEPTED_LAYER1|ACCEPTED_LAYER2) return 0;; esac   # NOT_ACCEPTED, or no label (acceptance failed) -> classified
  read -r cls act < <(aux $SUM_CMD stop-class --dir "$d" 2>> "$d/stop_class.err" | tail -1)
  [ -n "${act:-}" ] || { cls=unreadable; act=stop; }   # class not readable -> stop (as a failed G2 check)
  case "$act" in
    stop)
      grep -qx "$1" "$OUT/STOP" 2>/dev/null || echo "$1" >> "$OUT/STOP"
      log "STOP_NOT_ACCEPTED:$1:$cls:$(now) - $( [ "$cls" = g2 ] || [ "$cls" = unreadable ] && echo "G2 failed (structure or input)" || echo "batch reference run without a usable solution") (RUN_PLAN_DFX 3.3): no new solve starts; no retry, no parameter change; user decision";;
    unusable)
      grep -q "^$1 " "$OUT/UNUSABLE" 2>/dev/null || echo "$1 $cls $(now)" >> "$OUT/UNUSABLE"
      log "UNUSABLE:$1:$cls:$(now) - recorded unusable (not a reference run?); the batch goes on (no retry)";;
    *)
      log "NOT_ACCEPTED_REFERENCE_DEPENDENT:$1:$(c1_summary "$d/PRECISION.json") - C1 (b) / (c) only: no stop (RUN_PLAN_DFX 3.3)";;
  esac
}
export_run() {   # $1 rid -> export/<rid>/ (scrubbed logs; no LP / solution arrays, no raw solver log)
  local d="$OUT/$1" e="$EXP/$1" f; mkdir -p "$e"
  for f in RUN.json SOLVE_RECEIPT.json V5_GATES.json INTERIOR_CHECKS.json BUNKER_ACCOUNT.json GUROBI_LOG_SCRUBBED.txt RESOURCE.jsonl CO2_FLOWS.json GAP_TABLE.json \
           EMISSIONS_BY_COUNTRY.json CAPACITY_BY_TECH_COUNTRY.json cross_border_flows.csv COUNTRY_COST_LEDGER.csv COUNTRY_COST_LEDGER_USD2020.csv COUNTRY_COST_LEDGER_DETAIL.csv \
           LEDGER_IDENTITY.json NODAL_PRICES.csv DUALS_BY_CONSTRAINT.nc DUALS_INDEX.csv COMPONENT_COST_BREAKDOWN.csv COMPONENT_COST_BREAKDOWN_SUMMARY.json costs_active_research.csv \
           PRECISION.json PRECISION.md VIOLATIONS.json C1_ERR_TAIL.txt EXPORTS.json ALLOCATION.json ALLOCATION.csv ALLOCATION.md ALLOCATION_LINES.csv \
           V6_ACCEPTANCE.json V6_ACCEPTANCE_PROVISIONAL.json STOP_CLASS.json BUILD_CHECK.json; do
    [ -f "$d/$f" ] && cp "$d/$f" "$e/"
  done
  [ -d "$d/m12_owen" ] && { mkdir -p "$e/m12_owen"; cp "$d/m12_owen"/*.json "$d/m12_owen"/*.csv "$d/m12_owen"/*.md "$e/m12_owen/" 2>/dev/null; }
  [ -f "$d/solve.log" ] && grep -viE "$SCRUB" "$d/solve.log" > "$e/solve_log_scrubbed.txt"
  [ -f "$d/lp/MATH_PROBLEM.json" ] && cp "$d/lp/MATH_PROBLEM.json" "$e/"
  [ -f "$d/v5/kkt_summary.json" ] && cp "$d/v5/kkt_summary.json" "$e/"
  ls "$d"/*_solved.nc > /dev/null 2>&1 && cp "$d"/*_solved.nc "$e/"
  [ -f "$OUT/MONITOR_$1.csv" ] && cp "$OUT/MONITOR_$1.csv" "$e/"
  grep -A 30 "Command being timed" "$d/solve.err" > "$e/solve_time.txt" 2>/dev/null
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
    local bc; bc=$(aux $SUM_CMD build-check --dir "$d" --repo "$REPO" 2>> "$d/build_check.err"); log "BUILD_CHECK_$rid:$bc"
    export_run "$rid"; return 0
  fi
  [ -f "$d/.ended" ] || return 0
  local net sc lab rc ref=(); net=$(jget "$d/RUN.json" network); sc=$(jget "$d/RUN.json" scenario); lab=$(jget "$d/RUN.json" label)
  if [ ! -s "$net" ]; then   # POST_ONLY on another machine: the RUN.json path of the instance is absent - the registered network of this package, same SHA256 only
    local alt; alt=$(base_net "$rid")
    if [ -s "$alt" ] && [ "$(sha256sum "$alt" | cut -c1-64)" = "$(jget "$d/RUN.json" network_sha256)" ]; then log "NETWORK_PATH_$rid:$net absent here; using $alt (same SHA256)"; net=$alt
    else log "NETWORK_PATH_$rid:$net absent and no registered network with the same SHA256 here - violation analysis / C1 / Owen will not be computable"; fi
  fi
  [ -f "$OUT/BATCH_REFERENCE.json" ] && ref=(--reference "$OUT/BATCH_REFERENCE.json")
  if [ -f "$d/solution/X.npy" ] && [ ! -f "$d/VIOLATIONS.json" ]; then
    va_cmd "$rid" "$d" "$net" "$sc" "$lab"; rc=$?
    if [ $rc != 0 ]; then
      keep_failed "$d" VIOLATIONS.json c1_violations.log c1_violations.err
      va_cmd "$rid" "$d" "$net" "$sc" "$lab"; rc=$?; log "POSTPROC_RETRY:$rid:violations:exit=$rc:$(now)$( [ $rc = 0 ] && echo " - retry succeeded" || echo " - retry failed too; the registered rules apply (C1 not computable)")"
      [ $rc = 0 ] || keep_failed "$d" VIOLATIONS.json c1_violations.log c1_violations.err
    fi
    log "VIOLATIONS_$rid:exit=$rc"
  fi
  if [ ! -f "$d/PRECISION.json" ]; then
    c1_cmd "$rid" "$d" "$net" "$sc" "$lab" ${ref[@]+"${ref[@]}"}; rc=$?
    if [ $rc != 0 ]; then
      keep_failed "$d" PRECISION.json PRECISION.md c1_precision.log c1_precision.err
      c1_cmd "$rid" "$d" "$net" "$sc" "$lab" ${ref[@]+"${ref[@]}"}; rc=$?; log "POSTPROC_RETRY:$rid:c1:exit=$rc:$(now)$( [ $rc = 0 ] && echo " - retry succeeded" || echo " - retry failed too; the registered rules apply (C1 not computable)")"
      [ $rc = 0 ] || { grep -viE "$SCRUB" "$d/c1_precision.err" 2>/dev/null | tail -40 > "$d/C1_ERR_TAIL.txt"; keep_failed "$d" PRECISION.json PRECISION.md c1_precision.log c1_precision.err; }
    fi
    log "C1_$rid:exit=$rc:$( [ -f "$d/PRECISION.json" ] && c1_summary "$d/PRECISION.json" || echo missing):$( [ ${#ref[@]} -gt 0 ] && echo final || echo provisional)"
  fi
  if [ -f "$d/SOLVE_RECEIPT.json" ] && [ ! -f "$d/ALLOCATION.json" ]; then
    step "$rid" m12 $M12_CMD run --repo "$REPO" --solve-dir "$d" --scenario "$sc" --label "DFX_$rid" --out "$d" --register > "$d/m12.log" 2> "$d/m12.err"; log "M12_$rid:exit=$?"
  fi
  if [ -f "$d/solution/X.npy" ] && [ -f "$d/ALLOCATION.json" ] && [ ! -f "$d/m12_owen/OWEN.json" ]; then
    step "$rid" m12_owen /usr/bin/time -v $M12A_CMD audit --repo "$REPO" --network "$net" --scenario "$sc" --solve-dir "$d" --allocation "$d/ALLOCATION.json" \
        --tag "DFX_$rid" --out "$d/m12_owen" --register-dir "$d" ${TRUNC[@]+"${TRUNC[@]}"} > "$d/m12_owen.log" 2> "$d/m12_owen.err"; log "M12_OWEN_$rid:exit=$?"
  fi
  log "V6_$rid:$(accept "$rid"):$( [ -f "$d/PRECISION.json" ] && c1_summary "$d/PRECISION.json" | sed 's/.*:ref=/ref=/')"
  export_run "$rid"; stop_check "$rid"
}

# ---- batch reference and regrade (after the phase; idempotent)
regrade_all() {
  [ "$DRY" = 1 ] || [ "$BUILD_ONLY" = 1 ] && return 0
  if [ ! -f "$OUT/BATCH_REFERENCE.json" ]; then
    if [ -f "$OUT/V1/COUNTRY_COST_LEDGER.csv" ] && [ -f "$OUT/V2/COUNTRY_COST_LEDGER.csv" ]; then
      step batch reference $C1_CMD reference --integrated "$OUT/V1" --disconnected "$OUT/V2" --out "$OUT/BATCH_REFERENCE.json" > "$OUT/batch_reference.log" 2>&1
      log "BATCH_REFERENCE:exit=$?:$(now):V1=$(cat "$OUT/V1/.cond" 2>/dev/null):V2=$(cat "$OUT/V2/.cond" 2>/dev/null)"
    else
      log "BATCH_REFERENCE:not_available:V1/V2 ledgers missing - the runs keep the provisional default reference"; return 0
    fi
  fi
  [ -f "$OUT/BATCH_REFERENCE.json" ] || return 0
  local d rid
  for d in "$OUT"/V*/; do
    d=${d%/}; rid=${d##*/}; [ -f "$d/PRECISION.json" ] || continue
    c1_summary "$d/PRECISION.json" | grep -q ':ref=batch$' && continue
    [ -f "$d/V6_ACCEPTANCE.json" ] && cp "$d/V6_ACCEPTANCE.json" "$d/V6_ACCEPTANCE_PROVISIONAL.json"
    step "$rid" c1_regrade $C1_CMD regrade --solve-dir "$d" --reference "$OUT/BATCH_REFERENCE.json" > "$d/c1_regrade.log" 2>&1; local rc=$?
    if [ -f "$d/m12_owen/OWEN.json" ]; then
      step "$rid" owen_regrade $M12A_CMD regrade --owen "$d/m12_owen/OWEN.json" --precision "$d/PRECISION.json" --out "$d/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json" \
          > "$d/m12_owen_regrade.log" 2>&1
    fi
    log "REGRADE_$rid:exit=$rc:$(c1_summary "$d/PRECISION.json"):provisional=$(cat "$d/.label" 2>/dev/null):final=$(accept "$rid")"
    export_run "$rid"; stop_check "$rid"
  done
}

# ---- lanes and the phase
lane() {   # $1 lane name, then rids one after the other (>= LICENCE_GAP_S after the previous solve of the lane)
  local name=$1 prev="" rid; shift
  for rid in "$@"; do
    halted && { log "LANE_$name:$rid not started (batch halted)"; break; }
    solve_run "$rid" "${prev:+$OUT/$prev/.solve_end}" || break
    post_run "$rid"; prev=$rid
  done
}
phase() {   # $1 phase (SCHEDULE): lanes A and B side by side only with >= R_PAR_CORES container cores (RUN_PLAN_DFX 3.2), else one lane A then B
  halted && return 0
  phase_gap "$1"; halted && return 0
  local la lb one=() i; IFS=, read -ra la <<< "${LANE_A[$1]}"; IFS=, read -ra lb <<< "${LANE_B[$1]}"
  local thr=$(( $(max_threads "${la[@]}") + $(max_threads "${lb[@]}") ))
  if [ "$NOSOLVE" != 1 ] && [ "$NCORES" -ge "$R_PAR_CORES" ]; then
    log "PHASE_$1:two_lanes:A=${LANE_A[$1]}:B=${LANE_B[$1]}:threads=$thr:cores=$NCORES:min_cores=$R_PAR_CORES:$(now)"
    lane A "${la[@]}" & local a=$!; sleep 2; lane B "${lb[@]}" & local b=$!; wait $a; wait $b
  else
    for ((i = 0; i < ${#la[@]} || i < ${#lb[@]}; i++)); do [ $i -lt ${#la[@]} ] && one+=("${la[$i]}"); [ $i -lt ${#lb[@]} ] && one+=("${lb[$i]}"); done
    log "PHASE_$1:one_lane:$(IFS=,; echo "${one[*]}"):threads=$thr:cores=$NCORES:min_cores=$R_PAR_CORES$( [ "$NOSOLVE" = 1 ] && echo ':no_solve_mode'):$(now)"
    lane A "${one[@]}"
  fi
}
batch_post() {   # RUN_PLAN_DFX 3.4: B6 = V2 - V1 / M12 benefit, summary with the third-batch comparison; $1 = summary: only the summary and the batch export
  if [ "$BUILD_ONLY" != 1 ] && [ "$DRY" != 1 ] && [ "${1:-}" != summary ]; then
    if [ -f "$OUT/V1/ALLOCATION.json" ] && [ -f "$OUT/V2/ALLOCATION.json" ]; then
      step batch m12_benefit $M12_CMD benefit --repo "$REPO" --integrated "$OUT/V1" --disconnected "$OUT/V2" --out "$OUT/M12_BENEFIT" > "$OUT/M12_BENEFIT.log" 2>&1
      log "M12_BENEFIT:exit=$?:$(tail -1 "$OUT/M12_BENEFIT.log" 2>/dev/null)"
    else log "M12_BENEFIT:not_computable:V1 / V2 allocations missing"; fi
  fi
  local ref=(); [ -f "$HERE/BATCH3_REFERENCE_VALUES.json" ] && ref=(--reference "$HERE/BATCH3_REFERENCE_VALUES.json")
  aux $SUM_CMD summary --out-dir "$OUT" ${ref[@]+"${ref[@]}"} > "$OUT/summary.log" 2>&1; log "SUMMARY:exit=$?:reference=$([ ${#ref[@]} -gt 0 ] && echo batch3 || echo none):$(tail -1 "$OUT/summary.log" | cut -c1-300)"
  mkdir -p "$EXP/batch"
  for f in STATUS.txt BASE_CHECK.json BATCH_REFERENCE.json DFX_SUMMARY.json DFX_SUMMARY.md STOP STOP_SAFE UNUSABLE POSTPROC_ERRORS; do [ -f "$OUT/$f" ] && cp "$OUT/$f" "$EXP/batch/"; done
  [ -d "$OUT/M12_BENEFIT" ] && { mkdir -p "$EXP/batch/M12_BENEFIT"; cp -r "$OUT/M12_BENEFIT"/. "$EXP/batch/M12_BENEFIT/"; }
  [ -f "$HERE/BATCH3_REFERENCE_VALUES.json" ] && cp "$HERE/BATCH3_REFERENCE_VALUES.json" "$EXP/batch/"
}
pack() {   # $1 tag
  [ "$DRY" = 1 ] && return 0
  cp "$ST" "$EXP/batch/" 2>/dev/null
  local r; r=$(step batch pack $PACK_CMD "$OUT" "$1" 2>&1 | tail -1); log "PACK_$1:$r"
}

# ---- the batch
prepare || { log "HALTED:$(now):phase 0"; batch_post summary; pack halted_phase0; exit 3; }
phase 1
regrade_all
batch_post
UNU=$(cut -d' ' -f1 "$OUT/UNUSABLE" 2>/dev/null | paste -sd, -)
if halted; then
  pack halted
  log "HALTED:$(now):$(cat "$OUT/STOP" "$OUT/STOP_SAFE" 2>/dev/null | tr '\n' ' ')- waiting for the user (no retry, no parameter change):unusable=${UNU:-none}"
  exit 3
fi
pack final
log "DONE:$(now):unusable=${UNU:-none}"
exit 0
