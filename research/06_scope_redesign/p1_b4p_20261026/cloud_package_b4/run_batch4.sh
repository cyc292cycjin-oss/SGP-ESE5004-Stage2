#!/bin/bash
# B4P fourth-batch runner (instruction A4; RUN_PLAN_B4.md): the two FULL 2920x3h runs F1 (integrated) and F2 (disconnected) with the profile chosen
# by the third batch (formal_barrier_1e6_t16, Threads 16). Built from the third-batch runner run_batch3.sh (M10P / M10A / M10R): the same
# per-run post-processing chain (violations -> C1 with the batch's own reference and regrade -> M12 allocation + Owen dual form -> GATES_V6 ->
# graded class), the same process-group wall-clock kill, monitor, scrubbed exports, licence gaps, resume, test-hook guards and --repost mode;
# NEW (RUN_PLAN_B4 section 3): the split-process solve (SOLVE_MODE=split: process 1 s2_solve.py --split-stage build, process 2 b4_split_solve.py
# = the only Gurobi process, process 3 s2_solve.py --split-stage assign), the P1 probe (F2 starts beside F1 only when F1's memory peak within the
# first P1_WINDOW_S stays <= P1_THRESHOLD x quota and the container has >= P1_MIN_CORES cores), the memory stop (cgroup anon memory >
# MEMORY_STOP_FRACTION x quota -> STOP_SAFE:MEMORY), the early speed check (iterations 11-20 x reference count + elapsed > PROJECTION_FRACTION x
# TimeLimit -> STOP_SAFE:PROJECTION), the memory condition for post-processing beside the other solve. PREPARED ONLY: it runs on the cloud
# instance after the user has rented it and authorised the batch (separate execution instruction).
#
#   GRB_LICENSE_FILE=<licence path> PY=<env python> bash run_batch4.sh --auth "<user authorisation text>"
#   The same command again resumes in the same RUN_DIR (default runs/batch4): a solve that has ended is never repeated.
#   POST_ONLY=1 PY=... bash run_batch4.sh                 no solve: the post-processing of every ended run, batch reference, regrade, batch summary, packs
#   BUILD_ONLY=1 PY=... bash run_batch4.sh                dry run: every run with --stop-before-solve (SOLVE_MODE=single) or --split-stage build (split), no solver
#   PY=... bash run_batch4.sh --repost F1 --into <dir>   no solve: the post-processing of an ENDED run redone with the current code (as run_batch3.sh)
#   ... bash run_batch4.sh --only F1 --auth "<text>"     HPR (RUN_PLAN_HPC.md, two PBS jobs): ONE run of the table - phase 0, the same solve_run / post_run
#                                                       as the batch mode (split processes, monitor, memory stop, projection stop, per-run post-processing,
#                                                       graded stop), no P1 probe, no regrade / batch summary / pack (the batch job does them with
#                                                       POST_ONLY=1 in the same RUN_DIR); WAIT_START_OF=F1 makes F2's Gurobi process wait until F1's
#                                                       Gurobi process started >= LICENCE_GAP_S ago (or F1 ended); exit 3 when halted. Resume: the same
#                                                       command again - an ended run is skipped, a started-not-ended run is STOP_SAFE:INTERRUPTED.
#   BUILD_ONLY=1 ... bash run_batch4.sh --only F1        HPR: the dry run of ONE run (process 1 only)
# HPR (2026-10-27; RUN_PLAN_HPC.md; user decisions B1-B4): R_TL = 864,000 s / R_WALL = 871,200 s (B1); the registered networks are the v2 2920x3h
# networks of b4_batch4.py (B2); MEM_MEASURE=auto|cgroup|rss - the memory stop uses the cgroup anon memory of CGROUP_ROOT (a v2 directory, a v1 JOB
# directory or the v1 root layout) and falls back to the RSS sum of the Gurobi process group when no cgroup memory accounting is readable (RUN_PLAN_HPC 5).
#
# PRE-REGISTERED RULES (RUN_PLAN_B4.md section 3; registered before any 2920x3h result; single sources: this file's R_* constants and
# scripts_project/b4_batch4.py thresholds):
#   * one solve per run: no retry, no parameter change, no warm start; TimeLimit R_TL = 259,200 s (72 h); wall clock R_WALL on the Gurobi process
#     (TimeLimit + 2 x the measured build / LP read / export overhead, section 3.1); the wall-clock kill ends the whole process group;
#   * order: F1 first; the P1 probe for P1_WINDOW_S after the start of F1's Gurobi process; F2 beside F1 only when the probe passes, else after F1
#     (solve and post-processing); >= R_GAP s from the end of a Gurobi process to the next start and from the runner start to the first start;
#   * memory stop and early speed check as above (both STOP_SAFE: nothing else starts; a resource restart on a larger machine is a new RUN_DIR with
#     the user's authorisation, not a retry);
#   * acceptance GATES_V6 with the batch's own C1 reference (F1 / F2), provisional -> regrade; class by b4_batch4.py stop-class: G2 failed, no
#     returned solution or C1 (a) failed -> STOP (recorded UNUSABLE for nosol / c1a; two runs only, nothing "goes on"); (b)/(c) only -> no stop;
#   * post-processing beside the other run's solve only when the container's free anon memory >= POST_MEM_NEED_GIB, else queued until that solve ends;
#     every post step under timeout POST_TIMEOUT_S (3 x the measured estimate), violation analysis and C1 redone once after a failure (M10A D2);
#   * not covered -> safe stop (STOP_SAFE with the reason): a solve started but not ended on resume, a solver process running at start, a base
#     network whose SHA256 differs from the build receipt / the registered value, a missing input.
# Environment: PY, RUN_DIR, SOLVE_MODE (registered value R_MODE; another value only with ALLOW_UNREGISTERED=1), WALL_CAP_S / GUROBI_TIME_LIMIT_S /
# LICENCE_GAP_S (registered values; others refused unless ALLOW_UNREGISTERED=1), GRACE_S (30), MONITOR_S (60), CGROUP_ROOT (/sys/fs/cgroup),
# CORES (default: cgroup quota, else nproc), MEM_QUOTA_GIB (default: cgroup memory.max, else MemTotal), REMOVE_LP (1 = process 2 deletes the LP
# file after reading it: data-disk saving, RUN_PLAN_B4 section 5), POST_TIMEOUT_S, BUILD_TIMEOUT_S, ASSIGN_TIMEOUT_S, POST_MEM_NEED_GIB, PACK_TIMEOUT_S.
# Test hooks (tests and the local dry run only; a formal run refuses them): SOLVE_CMD, SPLIT_CMD, VA_CMD, C1_CMD, M12_CMD, M12A_CMD, G6_CMD, SUM_CMD,
# PACK_CMD, LEDGER_CMD, TRUNCATE, DRY=1, FAKE_*; P1_WINDOW_S / P1_THRESHOLD / P1_MIN_CORES / MEMORY_STOP_FRACTION / PROJECTION_FRACTION overrides.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
AUTH=""; REPOST_RID=""; INTO=""; ARRAYS=""; ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --auth) AUTH="$2"; shift 2;;
    --repost) REPOST_RID="$2"; shift 2;;
    --into) INTO="$2"; shift 2;;
    --arrays) ARRAYS="$2"; shift 2;;
    --only) ONLY="$2"; shift 2;;
    *) echo "unknown argument $1"; exit 2;;
  esac
done
abs() { case "$1" in "") echo "";; /*) echo "$1";; *) echo "$(pwd)/${1#./}";; esac; }   # B4P A3.2: every path argument absolute (the steps run after cd "$REPO")
INTO=$(abs "$INTO"); ARRAYS=$(abs "$ARRAYS")
REPO=${REPO:-$HERE/repo}; NETS=${NETS:-$HERE/networks}; OUT=${RUN_DIR:-$HERE/runs/batch4}; PY=${PY:-python}
REPO=$(abs "$REPO"); NETS=$(abs "$NETS"); OUT=$(abs "$OUT")
BUILD_ONLY=${BUILD_ONLY:-0}; DRY=${DRY:-0}; POST_ONLY=${POST_ONLY:-0}; TRUNCATE=${TRUNCATE:-}
S1MODE=0; [ -n "$REPOST_RID" ] && S1MODE=1
NOSOLVE=0; { [ "$BUILD_ONLY" = 1 ] || [ "$DRY" = 1 ] || [ "$POST_ONLY" = 1 ] || [ "$S1MODE" = 1 ]; } && NOSOLVE=1
if [ "$S1MODE" = 1 ] && { [ "$BUILD_ONLY" = 1 ] || [ "$DRY" = 1 ] || [ "$POST_ONLY" = 1 ]; }; then echo "REFUSED: --repost not together with BUILD_ONLY / POST_ONLY / DRY"; exit 2; fi
if [ "$S1MODE" = 1 ] && [ -z "$INTO" ]; then echo "REFUSED: --repost needs --into <new dir> (the original run folder is read only)"; exit 2; fi
if [ -n "$ARRAYS" ] && [ -z "$REPOST_RID" ]; then echo "REFUSED: --arrays <dir> belongs to --repost"; exit 2; fi
if [ -n "$ONLY" ] && { [ "$POST_ONLY" = 1 ] || [ "$S1MODE" = 1 ] || [ "$DRY" = 1 ]; }; then echo "REFUSED: --only is the solve mode of one run (or its BUILD_ONLY dry run); not together with POST_ONLY / DRY / --repost"; exit 2; fi
# ---- registered values (RUN_PLAN_HPC.md section 2 = user decision B1 of 2026-10-27, superseding RUN_PLAN_B4 3.1; changed only by a registered plan change before any result)
R_TL=864000; R_WALL=871200; R_GAP=330; R_MODE=split   # HPR B1: TimeLimit 240 h (was 259,200 s); wall clock = TimeLimit + 2 x 3,600 s (B4P 3.1 item 2: process 2 read + array write-out <= ~1 h at 2920); = b4_batch4.py TIME_LIMIT_S / WALL_CAP_S / LICENCE_GAP_S
WALL_CAP_S=${WALL_CAP_S:-$R_WALL}; GUROBI_TIME_LIMIT_S=${GUROBI_TIME_LIMIT_S:-$R_TL}; LICENCE_GAP_S=${LICENCE_GAP_S:-$R_GAP}; SOLVE_MODE=${SOLVE_MODE:-$R_MODE}
GRACE_S=${GRACE_S:-30}; MONITOR_S=${MONITOR_S:-60}; CGROUP_ROOT=${CGROUP_ROOT:-/sys/fs/cgroup}; REMOVE_LP=${REMOVE_LP:-1}
MEM_MEASURE=${MEM_MEASURE:-auto}; WAIT_START_OF=${WAIT_START_OF:-}; WAIT_START_MAX_S=${WAIT_START_MAX_S:-7200}   # HPR (RUN_PLAN_HPC 4-5): memory measure auto|cgroup|rss; F2 waits for F1's Gurobi start + gap (at most WAIT_START_MAX_S)
case "$MEM_MEASURE" in auto|cgroup|rss) ;; *) echo "REFUSED: MEM_MEASURE must be auto, cgroup or rss"; exit 2;; esac
POST_TIMEOUT_S=${POST_TIMEOUT_S:-10800}; BUILD_TIMEOUT_S=${BUILD_TIMEOUT_S:-3600}; ASSIGN_TIMEOUT_S=${ASSIGN_TIMEOUT_S:-32400}; PACK_TIMEOUT_S=${PACK_TIMEOUT_S:-7200}   # RUN_PLAN_B4 3.1 / 3.6: 3 x the A1 estimates
POST_MEM_NEED_GIB=${POST_MEM_NEED_GIB:-100}   # RUN_PLAN_B4 3.6: a post-processing step rebuilds the LP model (process-1 peak ~72-92 GiB at 2920) -> 100 GiB free anon memory
P1_WINDOW_S=${P1_WINDOW_S:-3600}; P1_THRESHOLD=${P1_THRESHOLD:-0.40}; P1_MIN_CORES=${P1_MIN_CORES:-33}
HOOKS_SET=$(for k in SOLVE_CMD SPLIT_CMD VA_CMD C1_CMD M12_CMD M12A_CMD G6_CMD SUM_CMD PACK_CMD LEDGER_CMD TRUNCATE $(compgen -A variable | grep -E '^FAKE_'); do [ -z "${!k:-}" ] || printf '%s,' "$k"; done)
FORMAL=0; [ "$NOSOLVE" = 0 ] && [ "${ALLOW_UNREGISTERED:-0}" != 1 ] && FORMAL=1
SOLVE_CMD=${SOLVE_CMD:-"$PY $REPO/scripts_project/s2_solve.py"}; SPLIT_CMD=${SPLIT_CMD:-"$PY $REPO/scripts_project/b4_split_solve.py"}
VA_CMD=${VA_CMD:-"$PY $REPO/scripts_project/l23_violation_analysis.py"}; C1_CMD=${C1_CMD:-"$PY $REPO/scripts_project/s4o_c1_precision.py"}
M12_CMD=${M12_CMD:-"$PY $REPO/scripts_project/m12_allocation.py"}; M12A_CMD=${M12A_CMD:-"$PY $REPO/scripts_project/m12_rhs_audit.py"}
G6_CMD=${G6_CMD:-"$PY $REPO/scripts_project/v5/gates_v6.py"}; SUM_CMD=${SUM_CMD:-"$PY $REPO/scripts_project/b4_batch4.py"}; PACK_CMD=${PACK_CMD:-"bash $HERE/pack_results.sh"}
LEDGER_CMD=${LEDGER_CMD:-"$PY $REPO/scripts_project/s4d_ledger_redo.py"}
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'
TRUNC=(); [ -n "$TRUNCATE" ] && TRUNC=(--truncate "$TRUNCATE")
if [ "${ALLOW_UNREGISTERED:-0}" != 1 ]; then
  for pair in "WALL_CAP_S:$WALL_CAP_S:$R_WALL" "GUROBI_TIME_LIMIT_S:$GUROBI_TIME_LIMIT_S:$R_TL" "LICENCE_GAP_S:$LICENCE_GAP_S:$R_GAP" "SOLVE_MODE:$SOLVE_MODE:$R_MODE"; do
    IFS=: read -r k v r <<< "$pair"; [ "$v" = "$r" ] || { echo "REFUSED: $k=$v differs from the registered value $r (RUN_PLAN_B4.md section 3)"; exit 2; }
  done
  [ -z "$TRUNCATE" ] || { echo "REFUSED: TRUNCATE is for smoke tests only"; exit 2; }
fi
case "$SOLVE_MODE" in single|split) ;; *) echo "REFUSED: SOLVE_MODE must be single or split"; exit 2;; esac
if [ "$FORMAL" = 1 ] && [ -n "$HOOKS_SET" ]; then echo "REFUSED: ${HOOKS_SET%,} set - test hooks are not allowed in a formal run (unset them; ALLOW_UNREGISTERED=1 is for tests and the local dry run only)"; exit 2; fi
if [ "$NOSOLVE" = 1 ] && [ -n "$AUTH" ]; then echo "REFUSED: --auth together with BUILD_ONLY / POST_ONLY / DRY / --repost - the no-solve modes take no authorisation text"; exit 2; fi
if [ "$NOSOLVE" = 1 ]; then
  LIC=/nonexistent/b4p_dry_run_no_licence
  [ -n "$AUTH" ] || AUTH="B4P no-solve mode (build-only / post-only / dry / repost)"
else
  : "${GRB_LICENSE_FILE:?set GRB_LICENSE_FILE to the licence path provided by the user}"
  [ -r "$GRB_LICENSE_FILE" ] || { echo "GRB_LICENSE_FILE is not readable"; exit 2; }
  LIC=$GRB_LICENSE_FILE
  [ -n "$AUTH" ] || { echo "REFUSED: --auth \"<user authorisation text>\" is required"; exit 2; }
fi
command -v setsid >/dev/null 2>&1 && command -v timeout >/dev/null 2>&1 && [ -x /usr/bin/time ] || { echo "REFUSED: setsid, timeout and GNU time at /usr/bin/time are required"; exit 2; }
if [ "$S1MODE" = 1 ]; then
  [ -d "$OUT" ] || { echo "REFUSED: run folder $OUT missing (nothing to re-post-process)"; exit 2; }
  ST="$INTO/STATUS.txt"; EXP="$INTO/export"; ERRF="$INTO/POSTPROC_ERRORS"; export TMPDIR="$INTO/tmp"
else
  mkdir -p "$OUT" "$OUT/export" "$OUT/tmp" || { echo "cannot create $OUT"; exit 2; }
  ST="$OUT/STATUS.txt"; EXP="$OUT/export"; ERRF="$OUT/POSTPROC_ERRORS"; export TMPDIR="$OUT/tmp"
fi
T_START=$(date +%s)
export PYTHONHASHSEED=0

now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$*" >> "$ST"; }
halted() { [ -f "$OUT/STOP_SAFE" ] || [ -f "$OUT/STOP" ]; }
safe_stop() { echo "$1" >> "$OUT/STOP_SAFE"; log "STOP_SAFE:$1:$(now) - nothing else starts; waiting for the user"; }
jget() { "$PY" -c "import json,sys
d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'):
    d=d.get(k) if isinstance(d, dict) else None
print('' if d is None else d)" "$1" "$2" 2>/dev/null; }
busy() {   # python processes only (M10A F1); --only (HPR): only the processes of THIS run's folder - the other run's job may share the node (an earlier runner of the same run still counts)
  local l; l=$(ps -eo args= | grep -E '[s]2_solve\.py|[b]4_split_solve\.py' | grep -vE '^(/usr/bin/)?time |^setsid |^env ')
  [ -z "$ONLY" ] || l=$(printf '%s\n' "$l" | grep -F -- "$OUT/$ONLY/")
  printf '%s\n' "$l" | grep -c .; }
gurobi_busy() { ps -eo args= | grep -E '[b]4_split_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }

# ---- run table (single source: scripts_project/b4_batch4.py RUNS)
declare -A SC BASE SET PROF COSTS
while IFS='|' read -r rid sc base set prof costs; do
  [ -n "$rid" ] || continue; SC[$rid]=$sc; BASE[$rid]=$base; SET[$rid]=$set; PROF[$rid]=$prof; COSTS[$rid]=$costs
done < <(cd "$REPO" && $SUM_CMD runtable)
[ "${#SC[@]}" = 2 ] || { echo "REFUSED: run table not readable from $REPO (got ${#SC[@]} runs)"; exit 2; }
if [ -n "$ONLY" ]; then
  [ -n "${SC[$ONLY]:-}" ] || { echo "REFUSED: --only $ONLY is not a run of the registered table (${!SC[*]})"; exit 2; }
  [ -z "$WAIT_START_OF" ] || [ -n "${SC[$WAIT_START_OF]:-}" ] || { echo "REFUSED: WAIT_START_OF=$WAIT_START_OF is not a run of the registered table"; exit 2; }
  [ "$WAIT_START_OF" != "$ONLY" ] || { echo "REFUSED: WAIT_START_OF must name the OTHER run"; exit 2; }
fi
ITERS_REF() { case "$1" in F1) echo 450;; F2) echo 250;; *) echo 450;; esac; }   # RUN_PLAN_B4 3.4 reference iteration counts (third batch: integrated 253-465, disconnected 116-228)
threads_of() { "$PY" - "$REPO" "$1" <<'P' 2>/dev/null || echo 0
import sys, yaml
from pathlib import Path
print(int(yaml.safe_load((Path(sys.argv[1]) / "configs/research/baseline.yaml").read_text())["research"]["solver"]["profiles"][sys.argv[2]].get("Threads", 0)))
P
}
declare -A THREADS; THREADS[formal_barrier_1e6_t16]=$(threads_of formal_barrier_1e6_t16); [ "${THREADS[formal_barrier_1e6_t16]}" -gt 0 ] 2>/dev/null || { echo "REFUSED: Threads of the profile not readable"; exit 2; }
detect_cores() {
  if [ -n "${CORES:-}" ]; then echo "$CORES"; return; fi
  local q p
  if [ -r "$CGROUP_ROOT/cpu.max" ]; then read -r q p < "$CGROUP_ROOT/cpu.max"; if [ "$q" != max ] && [ "${p:-0}" -gt 0 ] 2>/dev/null; then echo $(( q / p )); return; fi
  elif [ -r "$CGROUP_ROOT/cpu/cpu.cfs_quota_us" ] && [ -r "$CGROUP_ROOT/cpu/cpu.cfs_period_us" ]; then q=$(cat "$CGROUP_ROOT/cpu/cpu.cfs_quota_us"); p=$(cat "$CGROUP_ROOT/cpu/cpu.cfs_period_us")
    if [ "$q" -gt 0 ] 2>/dev/null && [ "$p" -gt 0 ] 2>/dev/null; then echo $(( q / p )); return; fi; fi
  nproc
}
NCORES=$(detect_cores)
# cgroup files (HPR: three layouts - a cgroup v2 directory [memory.stat anon / memory.max], a cgroup v1 JOB directory [memory.stat total_rss / memory.limit_in_bytes,
# as /sys/fs/cgroup/memory/<PBS job path>], the v1 root layout [memory/memory.stat rss / memory/memory.limit_in_bytes]); the file cache is never counted
# MEM_MEASURE=rss (HPR: the job body found no job cgroup): the cgroup files under CGROUP_ROOT are NOT this job's accounting (root or a shared service cgroup -
# other jobs' memory) and are not read at all (review F-07); the monitor's cgroup columns stay empty and the quota comes from MEM_QUOTA_GIB
cg_mem_limit_b() { local v="" f; [ "$MEM_MEASURE" = rss ] && { echo ""; return; }
  for f in "$CGROUP_ROOT/memory.max" "$CGROUP_ROOT/memory.limit_in_bytes" "$CGROUP_ROOT/memory/memory.limit_in_bytes"; do [ -r "$f" ] && { v=$(cat "$f"); break; }; done
  case "$v" in ""|max) echo "";; *) [ "${#v}" -ge 19 ] && echo "" || echo "$v";; esac; }
cg_mem_used_b() { local f; [ "$MEM_MEASURE" = rss ] && { echo ""; return; }; for f in "$CGROUP_ROOT/memory.current" "$CGROUP_ROOT/memory.usage_in_bytes" "$CGROUP_ROOT/memory/memory.usage_in_bytes"; do [ -r "$f" ] && { cat "$f"; return; }; done; echo ""; }
cg_anon_b() { local f; [ "$MEM_MEASURE" = rss ] && { echo ""; return; }
  if [ -r "$CGROUP_ROOT/memory.stat" ]; then f=$CGROUP_ROOT/memory.stat; elif [ -r "$CGROUP_ROOT/memory/memory.stat" ]; then f=$CGROUP_ROOT/memory/memory.stat; else echo ""; return; fi
  awk '$1 == "anon" {a=$2} $1 == "total_rss" {t=$2} $1 == "rss" {r=$2} END {if (a != "") print a; else if (t != "") print t; else if (r != "") print r}' "$f"; }
cg_anon_source() { local f; [ "$MEM_MEASURE" = rss ] && { echo "none(rss_mode)"; return; }; if [ -r "$CGROUP_ROOT/memory.stat" ]; then f=$CGROUP_ROOT/memory.stat; elif [ -r "$CGROUP_ROOT/memory/memory.stat" ]; then f=$CGROUP_ROOT/memory/memory.stat; else echo none; return; fi
  echo "$f:$(awk '$1 == "anon" {a=1} $1 == "total_rss" {t=1} $1 == "rss" {r=1} END {if (a) print "anon"; else if (t) print "total_rss"; else if (r) print "rss"; else print "nokey"}' "$f")"; }
group_rss_b() { local p r s=0; for p in $(pgrep -g "$1" 2>/dev/null); do r=$(ps -o rss= -p "$p" 2>/dev/null | tr -d ' '); [ -n "$r" ] && s=$((s + r * 1024)); done; echo "$s"; }   # RSS sum of a process group in bytes (RUN_PLAN_HPC 5: the fallback measure)
mem_measure_used() {   # HPR: which measure the memory stop uses in this environment (auto: cgroup anon when readable, else the process-group RSS)
  case "$MEM_MEASURE" in cgroup) echo cgroup;; rss) echo rss;; *) [ -n "$(cg_anon_b)" ] && echo cgroup || echo rss;; esac; }
detect_quota_gib() {
  if [ -n "${MEM_QUOTA_GIB:-}" ]; then echo "$MEM_QUOTA_GIB"; return; fi
  local l; l=$(cg_mem_limit_b); if [ -n "$l" ]; then awk -v b="$l" 'BEGIN {printf "%.2f", b/1073741824}'; else awk '/MemTotal/ {printf "%.2f", $2/1048576}' /proc/meminfo; fi
}
QUOTA_GIB=$(detect_quota_gib)
MEMORY_STOP_FRACTION=${MEMORY_STOP_FRACTION:-0.80}; PROJECTION_FRACTION=${PROJECTION_FRACTION:-0.80}
aux_threads() { local used=0 d rid k   # --only (HPR, review F-07): only THIS run's solve counts - the other run lives in another job / cgroup with its own cores
  for d in "$OUT"/F*/; do d=${d%/}; rid=${d##*/}; [ -z "$ONLY" ] || [ "$rid" = "$ONLY" ] || continue; [ -f "$d/.started" ] && [ ! -f "$d/.ended" ] && [ -n "${PROF[$rid]:-}" ] && used=$((used + ${THREADS[${PROF[$rid]}]})); done
  k=$((NCORES - used)); [ $k -ge 1 ] || k=1; echo $k; }
aux_env() { local k; k=$(aux_threads); echo "OMP_NUM_THREADS=$k MKL_NUM_THREADS=$k OPENBLAS_NUM_THREADS=$k NUMEXPR_MAX_THREADS=$k"; }
other_solve_running() { local d; [ -z "$ONLY" ] || return 1   # --only: the other run's solve is in another job (its own memory quota) - never a reason to queue this job's post-processing (review F-07)
  for d in "$OUT"/F*/; do d=${d%/}; [ -f "$d/.started" ] && [ ! -f "$d/.ended" ] && return 0; done; return 1; }
free_anon_gib() { local a; a=$(cg_anon_b); [ -n "$a" ] || { echo "$QUOTA_GIB"; return; }; awk -v q="$QUOTA_GIB" -v a="$a" 'BEGIN {printf "%.2f", q - a/1073741824}'; }
wait_for_memory() {   # RUN_PLAN_B4 3.6: a post-processing step beside the other run's solve only with POST_MEM_NEED_GIB free anon memory; else queued until that solve ends
  local rid=$1 name=$2 w=0
  while other_solve_running && [ "$(awk -v f="$(free_anon_gib)" -v n="$POST_MEM_NEED_GIB" 'BEGIN {print (f < n) ? 1 : 0}')" = 1 ]; do
    [ $w = 0 ] && log "POST_QUEUED:$rid:$name:free_anon=$(free_anon_gib)GiB<need=${POST_MEM_NEED_GIB}GiB:$(now) - queued until the other solve ends or memory frees"
    sleep "$MONITOR_S"; w=$((w + 1))
  done
  [ $w -gt 0 ] && log "POST_RESUMED:$rid:$name:$(now):waited=$((w * MONITOR_S))s"
}
keep_failed() { local d=$1 f n; shift; for f in "$@"; do [ -e "$d/$f" ] || continue; n=1; while [ -e "$d/$f.failed$n" ]; do n=$((n + 1)); done; mv "$d/$f" "$d/$f.failed$n"; done; }
step() {   # $1 rid $2 step name, then the command: licence removed, thread budget, timeout, memory condition; a non-zero exit is POSTPROC_ERROR and never changes the schedule
  local rid=$1 name=$2 rc t=$POST_TIMEOUT_S; shift 2; [ "$name" = pack ] && t=$PACK_TIMEOUT_S
  wait_for_memory "$rid" "$name"
  ( cd "$REPO" && exec env -u GRB_LICENSE_FILE $(aux_env) timeout -k 30 "$t" "$@" ); rc=$?
  [ $rc = 0 ] || { echo "$rid $name exit=$rc $(now)" >> "$ERRF"
    log "POSTPROC_ERROR:$rid:$name:exit=$rc$( { [ $rc = 124 ] || [ $rc = 137 ]; } && echo ":timeout_${t}s"):$(now) - recorded in POSTPROC_ERRORS; the schedule goes on (redo with POST_ONLY=1)"; }
  return $rc
}
aux() { ( cd "$REPO" && exec env -u GRB_LICENSE_FILE $(aux_env) timeout -k 30 "$POST_TIMEOUT_S" "$@" ); }
va_cmd() { step "$1" violations /usr/bin/time -v $VA_CMD --repo "$REPO" --solve-dir "$2" --network "$3" --scenario "$4" --label "$5" --out "$2/VIOLATIONS.json" ${TRUNC[@]+"${TRUNC[@]}"} > "$2/c1_violations.log" 2> "$2/c1_violations.err"; }
c1_cmd() { local rid=$1 d=$2 net=$3 sc=$4 lab=$5; shift 5
  step "$rid" c1 /usr/bin/time -v $C1_CMD run --repo "$REPO" --solve-dir "$d" --network "$net" --scenario "$sc" --label "$lab" --violations "$d/VIOLATIONS.json" "$@" ${TRUNC[@]+"${TRUNC[@]}"} > "$d/c1_precision.log" 2> "$d/c1_precision.err"; }

if [ -n "$REPOST_RID" ]; then
  rid=$REPOST_RID; [ -n "${SC[$rid]:-}" ] || { echo "REFUSED: --repost $rid is not a run of the registered table"; exit 2; }
  [ -f "$OUT/$rid/.ended" ] || { echo "REFUSED: --repost $rid has not ended"; exit 2; }
  [ -f "$OUT/$rid/RUN.json" ] && [ -f "$OUT/$rid/SOLVE_RECEIPT.json" ] || { echo "REFUSED: --repost $rid: RUN.json / SOLVE_RECEIPT.json missing"; exit 2; }
  [ -e "$INTO/$rid" ] && { echo "REFUSED: $INTO/$rid exists - every repost goes to a new folder"; exit 2; }
  mkdir -p "$INTO/export" "$INTO/tmp" || { echo "cannot create $INTO"; exit 2; }
fi
log "START:$(now):commit=$(cat "$HERE/COMMIT" 2>/dev/null || echo none):repo_commit=$(cat "$REPO/.package_commit" 2>/dev/null || echo none):mode=$( [ -n "$REPOST_RID" ] && echo "repost($REPOST_RID)" || { [ -n "$ONLY" ] && echo "only($ONLY)" || echo batch; }):solve_mode=$SOLVE_MODE:mem_measure=$MEM_MEASURE/$(mem_measure_used):cgroup_root=$CGROUP_ROOT:cgroup_anon_source=$(cg_anon_source):wait_start_of=${WAIT_START_OF:-none}:wait_start_max_s=$WAIT_START_MAX_S:build_only=$BUILD_ONLY:post_only=$POST_ONLY:dry=$DRY:cores=$NCORES:quota_gib=$QUOTA_GIB:threads_T16=${THREADS[formal_barrier_1e6_t16]}:time_limit_s=$GUROBI_TIME_LIMIT_S:wall_cap_s=$WALL_CAP_S:licence_gap_s=$LICENCE_GAP_S:p1=${P1_WINDOW_S}s/${P1_THRESHOLD}/${P1_MIN_CORES}cores:memory_stop=$MEMORY_STOP_FRACTION:projection=$PROJECTION_FRACTION:post_mem_need_gib=$POST_MEM_NEED_GIB:remove_lp=$REMOVE_LP:truncate=${TRUNCATE:-none}:resume=$([ -f "$OUT/.created" ] && echo yes || echo no):tmpdir=$TMPDIR:post_timeout_s=$POST_TIMEOUT_S:allow_unregistered=${ALLOW_UNREGISTERED:-0}:hooks=${HOOKS_SET%,}:into=${INTO:-none}:arrays=${ARRAYS:-none}"
[ "$FORMAL" = 0 ] && [ "$NOSOLVE" = 0 ] && log "NOTE:ALLOW_UNREGISTERED=1 in solve mode - tests only; hooks=${HOOKS_SET%,}"
[ "$S1MODE" = 1 ] || [ -f "$OUT/.created" ] || now > "$OUT/.created"

group_pids() { pgrep -g "$1" 2>/dev/null; }
group_alive() { [ -n "$(group_pids "$1")" ]; }
kill_group() { local pg=$1 g=0; kill -TERM -- "-$pg" 2>/dev/null; while group_alive "$pg" && [ $g -lt "$GRACE_S" ]; do sleep 1; g=$((g + 1)); done; group_alive "$pg" && { kill -KILL -- "-$pg" 2>/dev/null; return 9; }; return 0; }
monitor() {   # $1 pgid $2 rid $3 solve dir $4 interval s -> MONITOR_<rid>.csv (process-group RSS, cgroup used / anon / limit, host available, disk, last Gurobi line)
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
memory_exceeded() {   # $1 pgid of the Gurobi process group. RUN_PLAN_B4 3.3 / RUN_PLAN_HPC 5: the memory measure of this job (cgroup anon memory, no file cache; or, when no
  local a m                # cgroup memory accounting is readable / MEM_MEASURE=rss, the RSS sum of the process group) above MEMORY_STOP_FRACTION x quota
  m=$(mem_measure_used)
  if [ "$m" = cgroup ]; then a=$(cg_anon_b); [ -n "$a" ] || return 1; else a=$(group_rss_b "$1"); fi
  MEM_LAST_MEASURE="$m:$a"
  [ "$(awk -v a="$a" -v q="$QUOTA_GIB" -v f="$MEMORY_STOP_FRACTION" 'BEGIN {print (a/1073741824 > f*q) ? 1 : 0}')" = 1 ]
}
receipt_state() { [ -f "$1" ] || { echo missing; return; }; ( cd "$REPO" && $SUM_CMD receipt-state --receipt "$1" 2>/dev/null ) || echo unreadable; }
c1_summary() { "$PY" - "$1" <<'P' 2>/dev/null || echo unreadable
import json, sys
r = json.load(open(sys.argv[1])); g = r.get("grade", {}); a = r.get("acceptance", {}); src = str((r.get("reference") or {}).get("source", ""))
print(f"{g.get('grade')}:accepted={a.get('accepted')}:abc={int(bool(g.get('a')))}{int(bool(g.get('b')))}{int(bool(g.get('c')))}:ref={'batch' if src.startswith('this batch') else 'default'}")
P
}
base_net() { echo "$NETS/${BASE[$1]}_unsolved.nc"; }
base_scen() { echo "${BASE[$1]%%_*}"; }
registered_of() { jget "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" network.sha256; }

# ---- phase 0: inputs, the two base networks against the build receipts and the registered SHA256
prepare() {
  local f
  [ "$POST_ONLY" = 1 ] && { log "PREPARE:skipped (POST_ONLY)"; return 0; }
  for f in integrated_2920_3h_unsolved.nc disconnected_2920_3h_unsolved.nc integrated_BUILD_RECEIPT.json disconnected_BUILD_RECEIPT.json integrated_costs_active_research.csv disconnected_costs_active_research.csv; do
    [ -s "$NETS/$f" ] || { safe_stop "MISSING_INPUT:networks/$f"; return 1; }
  done
  [ "$DRY" = 1 ] || [ "$(busy)" = 0 ] || { safe_stop "SOLVER_PROCESS_RUNNING_AT_START:$(busy) solve processes (an earlier runner?)"; return 1; }
  local bc noreg=(); [ "${ALLOW_UNREGISTERED:-0}" = 1 ] && noreg=(--no-registered)   # stand-in tests on synthetic files: receipt checks kept, the registered SHA256 comparison recorded only
  bc=$(aux $SUM_CMD base-check --nets "$NETS" --out "$OUT/BASE_CHECK${ONLY:+_$ONLY}.json" ${noreg[@]+"${noreg[@]}"} 2>> "$OUT/prepare${ONLY:+_$ONLY}.err")   # --only: own file (F1 / F2 jobs share RUN_DIR)
  log "BASE_CHECK:$bc$( [ ${#noreg[@]} -gt 0 ] && echo ':registered_values_not_enforced (ALLOW_UNREGISTERED=1)')"; [ "$bc" = all_equal ] || { safe_stop "BASE_NETWORK_SHA256:$bc"; return 1; }
  return 0
}

# ---- one solve, never repeated
wait_gap() { [ "$NOSOLVE" = 1 ] || [ -z "$1" ] && return 0; while [ $(( $(date +%s) - $1 )) -lt "$LICENCE_GAP_S" ]; do sleep 5; done; log "GAP_$2:$(( $(date +%s) - $1 ))s:$(now)"; }
wait_other_start() {   # $1 rid. HPR (RUN_PLAN_HPC 4): with WAIT_START_OF=<other rid> this run's Gurobi process starts only >= LICENCE_GAP_S after the other run's Gurobi process
  local o=$WAIT_START_OF w=0 s   # started (its .solve_start, written by the other job's runner in the shared RUN_DIR), or after that run ended (.solve_end / .ended without a solve)
  [ -n "$o" ] && [ "$NOSOLVE" = 0 ] || return 0
  while :; do
    halted && return 0   # the caller checks halted next
    [ -f "$OUT/$o/.solve_end" ] && { log "WAIT_START_$1:$o ended its solve:$(now):waited=${w}s"; return 0; }
    if [ -f "$OUT/$o/.solve_start" ]; then s=$(cat "$OUT/$o/.solve_start"); [ $(( $(date +%s) - s )) -ge "$LICENCE_GAP_S" ] && { log "WAIT_START_$1:$o Gurobi started $(( $(date +%s) - s ))s ago (>= ${LICENCE_GAP_S}s):$(now):waited=${w}s"; return 0; }
    elif [ -f "$OUT/$o/.ended" ]; then log "WAIT_START_$1:$o ended without a Gurobi process ($(cat "$OUT/$o/.cond" 2>/dev/null)):$(now):waited=${w}s"; return 0; fi
    [ $w -lt "$WAIT_START_MAX_S" ] || { safe_stop "WAIT_START:$1:no Gurobi start marker of $o within ${WAIT_START_MAX_S}s (RUN_PLAN_HPC 4)"; return 1; }
    [ $w = 0 ] && log "WAIT_START_$1:waiting for $o/.solve_start + ${LICENCE_GAP_S}s (max ${WAIT_START_MAX_S}s):$(now)"
    sleep 5; w=$((w + 5))
  done
}
latest_solve_end() { local last=$T_START m f; for f in "$OUT"/*/.solve_end; do [ -f "$f" ] || continue; m=$(cat "$f"); [ "$m" -gt "$last" ] && last=$m; done; echo "$last"; }
write_run_json() {   # $1 rid $2 network $3 time limit $4 wall cap $5 label
  local d="$OUT/$1"
  "$PY" - "$d/RUN.json" "$1" "${SC[$1]}" "${BASE[$1]}" "${SET[$1]}" "${PROF[$1]}" "$NETS/${COSTS[$1]}_costs_active_research.csv" "$2" "$(sha256sum "$2" | cut -c1-64)" \
        "$(registered_of "$1")" "$3" "$4" "$5" "${TRUNCATE:-}" "$d" "$EXP/$1" "${THREADS[${PROF[$1]}]}" "$BUILD_ONLY" "$AUTH" "$SOLVE_MODE" "$(ITERS_REF "$1")" <<'P'
import json, sys, time
k = ["rid", "scenario", "base", "set", "profile", "costs_table", "network", "network_sha256", "registered_sha256", "time_limit", "wall_cap_s", "label", "truncate",
     "output", "export", "threads", "build_only", "authorization", "solve_mode", "iterations_reference"]
d = dict(zip(k, sys.argv[2:]))
d.update(time_limit=float(d["time_limit"]), wall_cap_s=int(d["wall_cap_s"]), threads=int(d["threads"]), build_only=d["build_only"] == "1", iterations_reference=int(d["iterations_reference"]),
         truncate=(int(d["truncate"]) if d["truncate"] else None), written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
json.dump(d, open(sys.argv[1], "w"), indent=1)
P
}
run_gurobi_process() {   # $1 rid $2 run dir $3 log $4 err, then the command: own process group, monitor, wall-clock kill, memory stop, early speed check -> sets KILLED_REASON
  local rid=$1 d=$2 lg=$3 er=$4; shift 4
  ( cd "$REPO" && exec setsid /usr/bin/time -v env GRB_LICENSE_FILE="$LIC" "$@" > "$lg" 2> "$er" ) &
  local pid=$! start; start=$(date +%s); sleep 1
  local pg; pg=$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  echo "$(now) pid=$pid pgid=$pg" > "$d/.started"; date +%s > "$d/.solve_start"
  log "SOLVE_$rid:pid=$pid:pgid=$pg:profile=${PROF[$rid]}:threads=${THREADS[${PROF[$rid]}]}:time_limit=$GUROBI_TIME_LIMIT_S:wall_cap=$WALL_CAP_S:network_sha256=$(jget "$d/RUN.json" network_sha256):mem_measure=$(mem_measure_used):cgroup_anon_source=$(cg_anon_source):quota_gib=$QUOTA_GIB:stop_gib=$(awk -v q="$QUOTA_GIB" -v f="$MEMORY_STOP_FRACTION" 'BEGIN {printf "%.2f", q*f}'):$(now)"
  monitor "$pg" "$rid" "$d" "$MONITOR_S" & local m=$! KILLED_REASON=""; local checked=0 tick=0; MEM_LAST_MEASURE=""
  while kill -0 "$pid" 2>/dev/null; do
    sleep 5; tick=$((tick + 5))
    if [ $(( $(date +%s) - start )) -ge "$WALL_CAP_S" ]; then
      log "KILLED_${WALL_CAP_S}S_$rid:$(now):group=$pg:members=$(group_pids "$pg" | tr '\n' ' ')"; KILLED_REASON=wall; kill_group "$pg" || log "KILL9_$rid:$(now)"; break
    fi
    if [ $((tick % MONITOR_S)) -lt 5 ]; then
      if memory_exceeded "$pg"; then
        log "MEMORY_STOP_$rid:$(now):measure=$MEM_LAST_MEASURE:bytes:quota_gib=$QUOTA_GIB:fraction_limit=$MEMORY_STOP_FRACTION"; KILLED_REASON=memory; kill_group "$pg" || log "KILL9_$rid:$(now)"; safe_stop "MEMORY:$rid:${MEM_LAST_MEASURE%%:*} memory above ${MEMORY_STOP_FRACTION} x quota (RUN_PLAN_B4 3.3 / RUN_PLAN_HPC 5)"; break
      fi
      if [ $checked = 0 ]; then
        local pr; pr=$(aux $SUM_CMD projection --dir "$d" --time-limit "$GUROBI_TIME_LIMIT_S" --iterations "$(ITERS_REF "$rid")" --now "$(( $(date +%s) - start ))" --out "$OUT/PROJECTION_$rid.json" 2>/dev/null); local prc=$?
        if [ $prc = 3 ]; then
          log "PROJECTION_STOP_$rid:$(now):$pr"; KILLED_REASON=projection; kill_group "$pg" || log "KILL9_$rid:$(now)"; safe_stop "PROJECTION:$rid:projected total above ${PROJECTION_FRACTION} x TimeLimit (RUN_PLAN_B4 3.4): $pr"; break
        elif [ $prc = 0 ]; then checked=1; log "PROJECTION_$rid:$(now):$pr - within the limit, no stop"; fi
      fi
    fi
  done
  wait "$pid" 2>/dev/null; local ex=$?
  local w=0; while group_alive "$pg" && [ $w -lt 120 ]; do sleep 1; w=$((w + 1)); done
  group_alive "$pg" && { kill -KILL -- "-$pg" 2>/dev/null; sleep 1; log "GROUP_SURVIVED_$rid:killed_after_120s"; }
  kill "$m" 2>/dev/null; wait "$m" 2>/dev/null
  date +%s > "$d/.solve_end"; echo "${KILLED_REASON:-none}" > "$d/.killed"
  return $ex
}
solve_run() {   # $1 rid: returns 1 when the batch must stop
  local rid=$1 d="$OUT/$1"; mkdir -p "$d"
  if [ -f "$d/.ended" ]; then log "SKIP_ENDED_$rid:$(cat "$d/.cond" 2>/dev/null) (ended before; never re-solved)"; return 0; fi
  if [ "$POST_ONLY" = 1 ]; then log "POST_ONLY_$rid:not solved - nothing to post-process"; return 0; fi
  if [ -f "$d/.started" ]; then safe_stop "INTERRUPTED_$rid:started $(cat "$d/.started") but never ended - not repeated (no retry); a resource restart is a new RUN_DIR with the user's authorisation"; return 1; fi
  local net; net=$(base_net "$rid"); [ -s "$net" ] || { safe_stop "MISSING_NETWORK_$rid:$net"; return 1; }
  local tl=$GUROBI_TIME_LIMIT_S wall=$WALL_CAP_S label=BATCH4_2920X3H
  [ -n "$TRUNCATE" ] && label=SMOKE_TEST_ONLY
  local cmd=($SOLVE_CMD --repo "$REPO" --network "$net" --scenario "${SC[$rid]}" --output "$d" --label "$label" --authorization "$AUTH; run $rid" --solver gurobi --solver-profile "${PROF[$rid]}" --scaling on --time-limit "$tl" --costs-table "$NETS/${COSTS[$rid]}_costs_active_research.csv" ${TRUNC[@]+"${TRUNC[@]}"})
  write_run_json "$rid" "$net" "$tl" "$wall" "$label"
  if [ "$DRY" = 1 ]; then log "DRY-RUN_$rid:${cmd[*]}"; return 0; fi
  local ex=0 rs cond t0; t0=$(date +%s)
  if [ "$SOLVE_MODE" = split ]; then
    # process 1: build + LP arrays + problem file (no licence); BUILD_ONLY: the same, nothing else
    if [ ! -f "$d/split/SPLIT_BUILD.json" ]; then
      ( cd "$REPO" && exec env -u GRB_LICENSE_FILE timeout -k 60 "$BUILD_TIMEOUT_S" /usr/bin/time -v "${cmd[@]}" --split-stage build > "$d/p1.log" 2> "$d/p1.err" ); ex=$?
      log "BUILD_$rid:exit=$ex:$(( $(date +%s) - t0 ))s:peak=$(grep -h 'Maximum resident' "$d/p1.err" 2>/dev/null | awk '{printf "%.2fGiB", $NF/1048576}'):lp_bytes=$(jget "$d/split/SPLIT_BUILD.json" problem_bytes):$(now)"
      [ $ex = 0 ] && [ -f "$d/split/SPLIT_BUILD.json" ] || { safe_stop "BUILD_FAILED_$rid:exit=$ex (process 1; no Gurobi call made)"; return 1; }
    fi
    if [ "$BUILD_ONLY" = 1 ]; then echo build_only > "$d/.cond"; echo 0 > "$d/.exit"; now > "$d/.ended"; log "RUN_$rid:split_built:exit=0:$(( $(date +%s) - t0 ))s"; return 0; fi
    wait_gap "$(latest_solve_end)" "$rid"
    wait_other_start "$rid" || return 1
    halted && { log "NOT_STARTED_$rid:batch halted during the gap"; return 1; }
    [ "$(gurobi_busy)" -lt 2 ] || { safe_stop "SOLVER_BUSY_$rid:$(gurobi_busy) Gurobi processes running"; return 1; }
    local pargs=(--run-dir "$d"); [ "$REMOVE_LP" = 1 ] && pargs+=(--remove-lp)
    run_gurobi_process "$rid" "$d" "$d/p2.log" "$d/p2.err" $SPLIT_CMD "${pargs[@]}"; ex=$?
    local S="$d/split/SPLIT_SOLVE.json"
    log "GUROBI_$rid:exit=$ex:killed=$(cat "$d/.killed"):status=$(jget "$S" gurobi_status_name):cond=$(jget "$S" termination_condition):iters=$(jget "$S" bar_iter_count):obj=$(jget "$S" objective):maxmem_gb=$(jget "$S" max_mem_used_gb):peak=$(grep -h 'Maximum resident' "$d/p2.err" 2>/dev/null | awk '{printf "%.2fGiB", $NF/1048576}'):$(( $(date +%s) - t0 ))s:$(now)"
    if [ -n "$(jget "$S" termination_condition)" ]; then   # process 3: map back + post-solve exports (no licence); every receipt field of the solve is already on disk
      ( cd "$REPO" && exec env -u GRB_LICENSE_FILE timeout -k 60 "$ASSIGN_TIMEOUT_S" /usr/bin/time -v "${cmd[@]}" --split-stage assign > "$d/p3.log" 2> "$d/p3.err" ); local ex3=$?
      log "ASSIGN_$rid:exit=$ex3:peak=$(grep -h 'Maximum resident' "$d/p3.err" 2>/dev/null | awk '{printf "%.2fGiB", $NF/1048576}'):post_errors=$(jget "$d/SOLVE_RECEIPT.json" post_solve_errors | cut -c1-200):$(now)"
    fi
  else
    [ "$BUILD_ONLY" = 1 ] && cmd+=(--stop-before-solve)
    if [ "$BUILD_ONLY" = 1 ]; then
      ( cd "$REPO" && exec env -u GRB_LICENSE_FILE timeout -k 60 "$BUILD_TIMEOUT_S" /usr/bin/time -v "${cmd[@]}" > "$d/solve.log" 2> "$d/solve.err" ); ex=$?
    else
      wait_gap "$(latest_solve_end)" "$rid"
      wait_other_start "$rid" || return 1
      halted && { log "NOT_STARTED_$rid:batch halted during the gap"; return 1; }
      [ "$(busy)" -lt 2 ] || { safe_stop "SOLVER_BUSY_$rid:$(busy) solve processes running"; return 1; }
      run_gurobi_process "$rid" "$d" "$d/solve.log" "$d/solve.err" "${cmd[@]}"; ex=$?
    fi
  fi
  rs=$(receipt_state "$d/SOLVE_RECEIPT.json"); local kr; kr=$(cat "$d/.killed" 2>/dev/null)
  if [ "$rs" = post_solve ]; then cond=$(jget "$d/SOLVE_RECEIPT.json" termination_condition); [ -n "$cond" ] || cond=none
  elif [ -n "$kr" ] && [ "$kr" != none ]; then cond="killed_$kr"   # the Gurobi process was terminated (wall / memory / projection): the receipt is still the pre-solve one
  elif [ "$rs" = stopped_before_solve ] || [ "$rs" = split_built ]; then cond=$rs
  else cond=none; fi
  echo "$cond" > "$d/.cond"; echo "$ex" > "$d/.exit"; now > "$d/.ended"
  log "RUN_$rid:$cond:exit=$ex:receipt=$rs:$(( $(date +%s) - t0 ))s:$(now)"
  halted && return 1
  return 0
}

# ---- post-processing of one run (as run_batch3.sh post_run; idempotent)
accept() { local d="${2:-$OUT/$1}" lab; lab=$(aux $G6_CMD accept --solve-dir "$d" --build-receipt "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" --repo "$REPO" 2>> "$d/v6.err" | tail -1); echo "$lab" > "$d/.label"; echo "$lab"; }
stop_check() {
  local d="${2:-$OUT/$1}" lab cls act; lab=$(cat "$d/.label" 2>/dev/null)
  if [ -n "$REPOST_RID" ]; then read -r cls act < <(aux $SUM_CMD stop-class --dir "$d" 2>> "$d/stop_class.err" | tail -1); log "REPOST_CLASS:$1:label=${lab:-none}:class=${cls:-unreadable}:registered_action=${act:-stop} - recorded only"; return 0; fi
  case "$lab" in ACCEPTED_LAYER1|ACCEPTED_LAYER2) return 0;; esac
  read -r cls act < <(aux $SUM_CMD stop-class --dir "$d" 2>> "$d/stop_class.err" | tail -1)
  [ -n "${act:-}" ] || { cls=unreadable; act=stop; }
  case "$act" in
    stop) grep -qx "$1" "$OUT/STOP" 2>/dev/null || echo "$1" >> "$OUT/STOP"; log "STOP_NOT_ACCEPTED:$1:$cls:$(now) - G2 failed (structure or input): no new solve starts; user decision";;
    stop_unusable|unusable) grep -q "^$1 " "$OUT/UNUSABLE" 2>/dev/null || echo "$1 $cls $(now)" >> "$OUT/UNUSABLE"; grep -qx "$1" "$OUT/STOP" 2>/dev/null || echo "$1" >> "$OUT/STOP"
      log "UNUSABLE:$1:$cls:$(now) - $( [ "$cls" = nosol ] && echo "no returned solution" || echo "C1 (a) failed") (RUN_PLAN_B4 3.5): recorded unusable; the batch stops (two runs only); user decision";;
    *) log "NOT_ACCEPTED_REFERENCE_DEPENDENT:$1:$(c1_summary "$d/PRECISION.json") - C1 (b) / (c) only: no stop";;
  esac
}
export_run() {
  local d="${2:-$OUT/$1}" e="$EXP/$1" f; mkdir -p "$e"
  for f in RUN.json SOLVE_RECEIPT.json V5_GATES.json INTERIOR_CHECKS.json BUNKER_ACCOUNT.json GUROBI_LOG_SCRUBBED.txt RESOURCE.jsonl CO2_FLOWS.json EMISSIONS_BY_COUNTRY.json CAPACITY_BY_TECH_COUNTRY.json \
           cross_border_flows.csv COUNTRY_COST_LEDGER.csv COUNTRY_COST_LEDGER_USD2020.csv COUNTRY_COST_LEDGER_DETAIL.csv LEDGER_IDENTITY.json NODAL_PRICES.csv DUALS_BY_CONSTRAINT.nc DUALS_INDEX.csv \
           COMPONENT_COST_BREAKDOWN.csv COMPONENT_COST_BREAKDOWN_SUMMARY.json costs_active_research.csv PRECISION.json PRECISION.md VIOLATIONS.json C1_ERR_TAIL.txt EXPORTS.json ALLOCATION.json ALLOCATION.csv \
           ALLOCATION.md ALLOCATION_LINES.csv V6_ACCEPTANCE.json V6_ACCEPTANCE_PROVISIONAL.json STOP_CLASS.json BUILD_CHECK.json; do [ -f "$d/$f" ] && cp "$d/$f" "$e/"; done
  for f in split/SPLIT_BUILD.json split/SPLIT_SOLVE.json split/RESOURCE_SOLVE.jsonl; do [ -f "$d/$f" ] && { mkdir -p "$e/split"; cp "$d/$f" "$e/split/"; }; done
  [ -d "$d/m12_owen" ] && { mkdir -p "$e/m12_owen"; cp "$d/m12_owen"/*.json "$d/m12_owen"/*.csv "$d/m12_owen"/*.md "$e/m12_owen/" 2>/dev/null; }
  for f in solve.log p1.log p2.log p3.log; do [ -f "$d/$f" ] && grep -viE "$SCRUB" "$d/$f" > "$e/${f%.log}_log_scrubbed.txt"; done
  [ -f "$d/lp/MATH_PROBLEM.json" ] && cp "$d/lp/MATH_PROBLEM.json" "$e/"; [ -f "$d/v5/kkt_summary.json" ] && cp "$d/v5/kkt_summary.json" "$e/"
  ls "$d"/*_solved.nc > /dev/null 2>&1 && cp "$d"/*_solved.nc "$e/"
  for f in "$OUT/MONITOR_$1.csv" "$OUT/PROJECTION_$1.json" "$OUT/P1_DECISION.json"; do [ -f "$f" ] && cp "$f" "$e/"; done
  for f in solve.err p2.err; do [ -f "$d/$f" ] && grep -A 30 "Command being timed" "$d/$f" > "$e/${f%.err}_time.txt" 2>/dev/null; done
  local c; c=$(cat "$d/.cond" 2>/dev/null)
  if [ -n "$c" ] && [ "$c" != optimal ] && [ "$c" != stopped_before_solve ] && [ "$c" != split_built ]; then
    tail -60 "$d/gurobi.linopy.log" 2>/dev/null | grep -viE "$SCRUB" > "$e/LOG_TAIL_NONOPTIMAL.txt"; for f in solve.err p2.err; do [ -f "$d/$f" ] && tail -60 "$d/$f" | grep -viE "$SCRUB" > "$e/STDERR_TAIL_NONOPTIMAL.txt"; done
  fi
}
post_run() {
  local rid=$1 d="${2:-$OUT/$1}"
  [ "$DRY" = 1 ] && return 0; [ -f "$d/RUN.json" ] || return 0
  if [ "$BUILD_ONLY" = 1 ]; then local bc; bc=$(aux $SUM_CMD build-check --dir "$d" --repo "$REPO" 2>> "$d/build_check.err"); log "BUILD_CHECK_$rid:$bc"; export_run "$rid"; return 0; fi
  [ -f "$d/.ended" ] || return 0
  local net sc lab rc ref=(); net=$(jget "$d/RUN.json" network); sc=$(jget "$d/RUN.json" scenario); lab=$(jget "$d/RUN.json" label)
  if [ ! -s "$net" ]; then local alt; alt=$(base_net "$rid")
    if [ -s "$alt" ] && [ "$(sha256sum "$alt" | cut -c1-64)" = "$(jget "$d/RUN.json" network_sha256)" ]; then log "NETWORK_PATH_$rid:$net absent here; using $alt (same SHA256)"; net=$alt; else log "NETWORK_PATH_$rid:$net absent - violation analysis / C1 / Owen not computable"; fi; fi
  [ -f "$OUT/BATCH_REFERENCE.json" ] && ref=(--reference "$OUT/BATCH_REFERENCE.json")
  if [ -f "$d/solution/X.npy" ] && [ ! -f "$d/VIOLATIONS.json" ]; then
    va_cmd "$rid" "$d" "$net" "$sc" "$lab"; rc=$?
    if [ $rc != 0 ]; then keep_failed "$d" VIOLATIONS.json c1_violations.log c1_violations.err; va_cmd "$rid" "$d" "$net" "$sc" "$lab"; rc=$?
      log "POSTPROC_RETRY:$rid:violations:exit=$rc:$(now)$( [ $rc = 0 ] && echo " - retry succeeded" || echo " - retry failed too (C1 not computable)")"; [ $rc = 0 ] || keep_failed "$d" VIOLATIONS.json c1_violations.log c1_violations.err; fi
    log "VIOLATIONS_$rid:exit=$rc"
  fi
  if [ ! -f "$d/PRECISION.json" ]; then
    c1_cmd "$rid" "$d" "$net" "$sc" "$lab" ${ref[@]+"${ref[@]}"}; rc=$?
    if [ $rc != 0 ]; then keep_failed "$d" PRECISION.json PRECISION.md c1_precision.log c1_precision.err; c1_cmd "$rid" "$d" "$net" "$sc" "$lab" ${ref[@]+"${ref[@]}"}; rc=$?
      log "POSTPROC_RETRY:$rid:c1:exit=$rc:$(now)$( [ $rc = 0 ] && echo " - retry succeeded" || echo " - retry failed too (C1 not computable)")"
      [ $rc = 0 ] || { grep -viE "$SCRUB" "$d/c1_precision.err" 2>/dev/null | tail -40 > "$d/C1_ERR_TAIL.txt"; keep_failed "$d" PRECISION.json PRECISION.md c1_precision.log c1_precision.err; }; fi
    log "C1_$rid:exit=$rc:$( [ -f "$d/PRECISION.json" ] && c1_summary "$d/PRECISION.json" || echo missing):$( [ ${#ref[@]} -gt 0 ] && echo final || echo provisional)"
  fi
  if [ -f "$d/SOLVE_RECEIPT.json" ] && [ ! -f "$d/ALLOCATION.json" ]; then
    step "$rid" m12 $M12_CMD run --repo "$REPO" --solve-dir "$d" --scenario "$sc" --label "BATCH4_$rid" --out "$d" --register > "$d/m12.log" 2> "$d/m12.err"; log "M12_$rid:exit=$?"
  fi
  if [ -f "$d/solution/X.npy" ] && [ -f "$d/ALLOCATION.json" ] && [ ! -f "$d/m12_owen/OWEN.json" ]; then
    step "$rid" m12_owen /usr/bin/time -v $M12A_CMD audit --repo "$REPO" --network "$net" --scenario "$sc" --solve-dir "$d" --allocation "$d/ALLOCATION.json" --tag "BATCH4_$rid" --out "$d/m12_owen" --register-dir "$d" ${TRUNC[@]+"${TRUNC[@]}"} > "$d/m12_owen.log" 2> "$d/m12_owen.err"; log "M12_OWEN_$rid:exit=$?"
  fi
  log "V6_$rid:$(accept "$rid" "$d"):$( [ -f "$d/PRECISION.json" ] && c1_summary "$d/PRECISION.json" | sed 's/.*:ref=/ref=/')"
  export_run "$rid" "$d"; stop_check "$rid" "$d"
}
regrade_all() {
  [ "$DRY" = 1 ] || [ "$BUILD_ONLY" = 1 ] && return 0
  if [ ! -f "$OUT/BATCH_REFERENCE.json" ]; then
    if [ -f "$OUT/F1/COUNTRY_COST_LEDGER.csv" ] && [ -f "$OUT/F2/COUNTRY_COST_LEDGER.csv" ]; then
      step batch reference $C1_CMD reference --integrated "$OUT/F1" --disconnected "$OUT/F2" --out "$OUT/BATCH_REFERENCE.json" > "$OUT/batch_reference.log" 2>&1
      log "BATCH_REFERENCE:exit=$?:$(now):F1=$(cat "$OUT/F1/.cond" 2>/dev/null):F2=$(cat "$OUT/F2/.cond" 2>/dev/null)"
    else log "BATCH_REFERENCE:not_available:F1/F2 ledgers missing - the runs keep the provisional default reference"; return 0; fi
  fi
  [ -f "$OUT/BATCH_REFERENCE.json" ] || return 0
  local d rid
  for d in "$OUT"/F*/; do
    d=${d%/}; rid=${d##*/}; [ -f "$d/PRECISION.json" ] || continue
    c1_summary "$d/PRECISION.json" | grep -q ':ref=batch$' && continue
    [ -f "$d/V6_ACCEPTANCE.json" ] && cp "$d/V6_ACCEPTANCE.json" "$d/V6_ACCEPTANCE_PROVISIONAL.json"
    step "$rid" c1_regrade $C1_CMD regrade --solve-dir "$d" --reference "$OUT/BATCH_REFERENCE.json" > "$d/c1_regrade.log" 2>&1; local rc=$?
    [ -f "$d/m12_owen/OWEN.json" ] && step "$rid" owen_regrade $M12A_CMD regrade --owen "$d/m12_owen/OWEN.json" --precision "$d/PRECISION.json" --out "$d/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json" > "$d/m12_owen_regrade.log" 2>&1
    log "REGRADE_$rid:exit=$rc:$(c1_summary "$d/PRECISION.json"):provisional=$(cat "$d/.label" 2>/dev/null):final=$(accept "$rid")"
    export_run "$rid"; stop_check "$rid"
  done
}
batch_post() {
  if [ "$BUILD_ONLY" != 1 ] && [ "$DRY" != 1 ] && [ "${1:-}" != summary ]; then
    if [ -f "$OUT/F1/ALLOCATION.json" ] && [ -f "$OUT/F2/ALLOCATION.json" ]; then
      step batch m12_benefit $M12_CMD benefit --repo "$REPO" --integrated "$OUT/F1" --disconnected "$OUT/F2" --out "$OUT/M12_BENEFIT" > "$OUT/M12_BENEFIT.log" 2>&1
      log "M12_BENEFIT:exit=$?:$(tail -1 "$OUT/M12_BENEFIT.log" 2>/dev/null)"
    else log "M12_BENEFIT:not_computable:F1 / F2 allocations missing"; fi
  fi
  local b3=(); [ -n "${BATCH3_EXPORT:-}" ] && [ -d "${BATCH3_EXPORT}" ] && b3=(--batch3 "$BATCH3_EXPORT")
  [ -n "${REFERENCE_VALUES:-}" ] && [ -f "${REFERENCE_VALUES}" ] && b3+=(--reference-values "$REFERENCE_VALUES")   # HPR (RUN_PLAN_HPC 7.4): third batch / DFX reference VALUES (numbers only; description)
  aux $SUM_CMD summary --out-dir "$OUT" ${b3[@]+"${b3[@]}"} > "$OUT/summary.log" 2>&1; log "SUMMARY:exit=$?:$(tail -1 "$OUT/summary.log" | cut -c1-300)"
  mkdir -p "$EXP/batch"
  for f in STATUS.txt BASE_CHECK.json BATCH_REFERENCE.json BATCH4_SUMMARY.json BATCH4_SUMMARY.md STOP STOP_SAFE UNUSABLE POSTPROC_ERRORS P1_DECISION.json PROJECTION_F1.json PROJECTION_F2.json; do [ -f "$OUT/$f" ] && cp "$OUT/$f" "$EXP/batch/"; done
  [ -d "$OUT/M12_BENEFIT" ] && { mkdir -p "$EXP/batch/M12_BENEFIT"; cp -r "$OUT/M12_BENEFIT"/. "$EXP/batch/M12_BENEFIT/"; }
}
pack() { [ "$DRY" = 1 ] && return 0; local root=$OUT; [ "$S1MODE" = 1 ] && root=$INTO; [ -n "${2:-}" ] || cp "$ST" "$EXP/batch/" 2>/dev/null
  local r; r=$(step batch pack $PACK_CMD "$root" "$1" ${2:+"$2"} ${3:+"$3"} ${4:+"$4"} 2>&1 | tail -1); log "PACK_$1:$r"; }

# ---- --repost (as run_batch3.sh)
if [ -n "$REPOST_RID" ]; then
  rid=$REPOST_RID; src="$OUT/$rid"; new="$INTO/$rid"; arrays="${ARRAYS:-$OUT/$rid}"
  nc=$(ls "$src"/*_solved.nc 2>/dev/null | head -1); [ -n "$nc" ] || nc=$(ls "$OUT/export/$rid"/*_solved.nc 2>/dev/null | head -1)
  [ -n "$nc" ] && [ -s "$nc" ] || { echo "REFUSED: no solved network of $rid"; exit 2; }
  [ -f "$arrays/lp/MATH_PROBLEM.json" ] && [ -f "$arrays/solution/X.npy" ] || { echo "REFUSED: LP / solution arrays of $rid missing under $arrays (lp/, solution/)"; exit 2; }
  mkdir -p "$new/v5"
  for f in RUN.json SOLVE_RECEIPT.json V5_GATES.json INTERIOR_CHECKS.json BUNKER_ACCOUNT.json GUROBI_LOG_SCRUBBED.txt RESOURCE.jsonl CO2_FLOWS.json EMISSIONS_BY_COUNTRY.json CAPACITY_BY_TECH_COUNTRY.json cross_border_flows.csv EXPORTS.json COMPONENT_COST_BREAKDOWN.csv COMPONENT_COST_BREAKDOWN_SUMMARY.json costs_active_research.csv DUALS_INDEX.csv .cond .exit .ended .started .solve_end; do [ -f "$src/$f" ] && cp "$src/$f" "$new/"; done
  [ -f "$src/v5/kkt_summary.json" ] && cp "$src/v5/kkt_summary.json" "$new/v5/"
  ln -s "$nc" "$new/$(basename "$nc")"; [ -f "$src/DUALS_BY_CONSTRAINT.nc" ] && ln -s "$src/DUALS_BY_CONSTRAINT.nc" "$new/DUALS_BY_CONSTRAINT.nc"; ln -s "$arrays/lp" "$new/lp"; ln -s "$arrays/solution" "$new/solution"
  log "REPOST_$rid:$(now):source=$src:into=$new:arrays=$arrays:label_before=$(jget "$src/V6_ACCEPTANCE.json" label)"
  step "$rid" ledger $LEDGER_CMD --solve-dir "$src" --into "$new" --repo "$REPO" > "$new/ledger_redo.log" 2> "$new/ledger_redo.err"; log "LEDGER_$rid:exit=$?"
  post_run "$rid" "$new"
  pack "repost_$rid" "export/$rid" "export/$rid/ARRAYS_MANIFEST.json" "$rid"
  log "DONE_REPOST:$(now):$rid:label_before=$(jget "$src/V6_ACCEPTANCE.json" label):label_after=$(cat "$new/.label" 2>/dev/null)"; exit 0
fi

# ---- --only <rid> (HPR two-job method, RUN_PLAN_HPC 3-5 / 7.3): phase 0, the one run's solve_run / post_run exactly as in the batch, no P1 probe; the batch
#      job (POST_ONLY=1, same RUN_DIR) does regrade / B6 / summary / packs; exit 3 when halted (a STOP / STOP_SAFE of either run halts both jobs' solves)
if [ -n "$ONLY" ]; then
  log "ONLY_MODE:$(now):run=$ONLY:p1_probe=not_used:wait_start_of=${WAIT_START_OF:-none}:shared_run_dir=$OUT - regrade / B6 / summary / packs by the batch job (POST_ONLY=1)"
  prepare || { log "HALTED_ONLY:$(now):$ONLY:phase 0"; exit 3; }
  wait_gap "$(latest_solve_end)" "PHASE_1_$ONLY"
  if halted; then log "NOT_STARTED_$ONLY:halted before the start:$(cat "$OUT/STOP" "$OUT/STOP_SAFE" 2>/dev/null | tr '\n' ' ')"
  else solve_run "$ONLY"; post_run "$ONLY"; fi
  [ -f "$OUT/.created" ] && cp "$ST" "$EXP/STATUS_only_$ONLY.txt" 2>/dev/null
  if halted; then log "HALTED_ONLY:$(now):$ONLY:$(cat "$OUT/STOP" "$OUT/STOP_SAFE" 2>/dev/null | tr '\n' ' ')- waiting for the user (no retry, no parameter change)"; exit 3; fi
  log "DONE_ONLY:$(now):$ONLY:$(cat "$OUT/$ONLY/.cond" 2>/dev/null):label=$(cat "$OUT/$ONLY/.label" 2>/dev/null)"; exit 0
fi

# ---- the batch: F1, the P1 probe, F2 beside or after F1
prepare || { log "HALTED:$(now):phase 0"; batch_post summary; pack halted_phase0; exit 3; }
wait_gap "$(latest_solve_end)" PHASE_1
if ! halted; then
  solve_run F1 & LANE_F1=$!
  if [ "$NOSOLVE" = 1 ]; then   # no Gurobi process: one lane, F1 then F2 (BUILD_ONLY builds both; POST_ONLY post-processes both)
    wait $LANE_F1; post_run F1; halted || { solve_run F2; post_run F2; }
  else
    # P1 probe: wait until F1's Gurobi process has run P1_WINDOW_S (or ended), then decide (b4_batch4.py p1); F2 beside F1 only when the probe passes
    until [ -f "$OUT/F1/.solve_start" ] || ! kill -0 $LANE_F1 2>/dev/null; do sleep 5; done
    if [ -f "$OUT/F1/.solve_start" ]; then
      s0=$(cat "$OUT/F1/.solve_start")
      while kill -0 $LANE_F1 2>/dev/null && [ ! -f "$OUT/F1/.solve_end" ] && [ $(( $(date +%s) - s0 )) -lt "$P1_WINDOW_S" ]; do sleep 10; done
      pd=$(aux $SUM_CMD p1 --monitor "$OUT/MONITOR_F1.csv" --quota-gib "$QUOTA_GIB" --cores "$NCORES" --threshold "$P1_THRESHOLD" --min-cores "$P1_MIN_CORES" --window-s "$P1_WINDOW_S" --out "$OUT/P1_DECISION.json" 2>/dev/null); prc=$?
      log "P1_PROBE:$(now):$pd:decision=$( [ $prc = 0 ] && echo parallel || echo after_F1)"
      if [ $prc = 0 ] && kill -0 $LANE_F1 2>/dev/null && ! halted; then
        solve_run F2 & LANE_F2=$!; wait $LANE_F2; post_run F2; wait $LANE_F1; post_run F1
      else
        wait $LANE_F1; post_run F1; halted || { solve_run F2; post_run F2; }
      fi
    else
      wait $LANE_F1; post_run F1
    fi
  fi
fi
regrade_all
batch_post
UNU=$(cut -d' ' -f1 "$OUT/UNUSABLE" 2>/dev/null | paste -sd, -)
if halted; then pack halted; log "HALTED:$(now):$(cat "$OUT/STOP" "$OUT/STOP_SAFE" 2>/dev/null | tr '\n' ' ')- waiting for the user (no retry, no parameter change):unusable=${UNU:-none}"; exit 3; fi
pack final
log "DONE:$(now):unusable=${UNU:-none}"
exit 0
