#!/bin/bash
# B4P fourth-batch package preflight (RUN_PLAN_B4.md section 5), inside the unpacked package folder on the instance; no solve.
#   PY=<environment python> GRB_LICENSE_FILE=<licence path> bash preflight.sh
# Sections (PREFLIGHT_ONLY = comma list; default all):
#   guards     none of the test hooks / dry-run switches of run_batch4.sh is set in this shell (M10A B5.5)
#   sha        SHA256SUMS of every package file; unpacks code_<COMMIT8>.tar.gz to ./repo (an older ./repo of another commit is moved aside)
#   networks   the two FULL 2920x3h base networks against their build receipts AND the registered SHA256 / bytes (b4_batch4.py base-check)
#   env        environment against env/ENV_LOCK.txt (env/env_check.py: key packages identical)
#   profile    profile formal_barrier_1e6_t16: s2_solve.py key-name check, interior-point gate path, Threads 16; TimeLimit = registered value
#   code       the run / post-processing modules import without the licence (s2_solve, b4_split_solve, b4_batch4, l23_violation_analysis,
#              s4o_c1_precision, m12_allocation, m12_rhs_audit, gates_v6); the run table has 2 runs; s2_solve has --split-stage
#   tools      GNU time (-v) at /usr/bin/time, setsid, pgrep, timeout, tmux (warning only)
#   licence    GRB_LICENSE_FILE readable and accepted by Gurobi - output suppressed, nothing printed; holds one WLS token >= 5 min (330 s gap)
#   resources  container cgroup quota (cores, memory), free data disk under this folder (PREFLIGHT_DISK_PATH override) against the HARD FLOOR of
#              RUN_PLAN_B4.md section 5: cores >= NEED_CORES, memory >= NEED_MEM_GIB, free disk >= NEED_DISK_GB (values registered from A1)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
PY="${PY:-python}"; ok=1; USER_CGROUP_ROOT="${CGROUP_ROOT:-}"; CGROUP_ROOT="${CGROUP_ROOT:-/sys/fs/cgroup}"; ONLY="${PREFLIGHT_ONLY:-guards,sha,networks,env,profile,code,tools,licence,resources}"   # HPR H3.5: the default is set AFTER remembering whether the user set it (the guards note used to fire on the default itself)
NEED_CORES=${NEED_CORES:-25}; NEED_MEM_GIB=${NEED_MEM_GIB:-190}; NEED_DISK_GB=${NEED_DISK_GB:-45}; R_TL=864000   # hard floor (RUN_PLAN_B4 section 5: F1 split process-2 high estimate 160 GiB / 0.80 = 200 -> 190 GiB rounded to the 240 GB class; disk ~36 GB persistent + 5.4 GB transient); R_TL = RUN_PLAN_HPC section 2 (B1; was 259,200), asserted against b4_batch4.py / run_batch4.sh in the code section
sec() { case ",$ONLY," in *",$1,"*) return 0;; *) return 1;; esac; }
if sec guards; then
  echo "== guards: test hooks / dry-run switches in this shell"; bad=()
  for k in ALLOW_UNREGISTERED BUILD_ONLY POST_ONLY DRY TRUNCATE SOLVE_CMD SPLIT_CMD VA_CMD C1_CMD M12_CMD M12A_CMD G6_CMD SUM_CMD PACK_CMD LEDGER_CMD WALL_CAP_S GUROBI_TIME_LIMIT_S LICENCE_GAP_S GRACE_S MONITOR_S POST_TIMEOUT_S PACK_TIMEOUT_S SOLVE_MODE P1_WINDOW_S P1_THRESHOLD P1_MIN_CORES MEMORY_STOP_FRACTION PROJECTION_FRACTION BUILD_TIMEOUT_S ASSIGN_TIMEOUT_S POST_MEM_NEED_GIB WAIT_START_MAX_S $(compgen -A variable | grep -E '^FAKE_'); do
    [ -z "${!k:-}" ] || bad+=("$k")
  done
  if [ ${#bad[@]} -gt 0 ]; then echo "SET IN THIS SHELL - unset before the formal run: ${bad[*]}"; ok=0; else echo "no test hook / dry-run switch set"; fi
  for k in RUN_DIR CORES MEM_QUOTA_GIB REPO NETS TMPDIR PREFLIGHT_DISK_PATH REMOVE_LP BATCH3_EXPORT MEM_MEASURE WAIT_START_OF; do [ -z "${!k:-}" ] || echo "NOTE: $k=${!k} (operational override; make sure it is intended)"; done
  [ -z "$USER_CGROUP_ROOT" ] || echo "NOTE: CGROUP_ROOT=$USER_CGROUP_ROOT (operational override; make sure it is intended)"
fi
if sec sha; then
  echo "== SHA256SUMS"; sha256sum -c --quiet SHA256SUMS && echo "all $(wc -l < SHA256SUMS) files OK" || { echo "CHECKSUM MISMATCH"; ok=0; }
  C8=$(cut -c1-8 COMMIT)
  if [ -d repo ] && [ "$(cat repo/.package_commit 2>/dev/null)" != "$(cat COMMIT)" ]; then
    old=$(cut -c1-8 repo/.package_commit 2>/dev/null || true); mv repo "repo_prev_${old:-unknown}_$(date -u +%Y%m%dT%H%M%SZ)" && echo "older ./repo moved aside (not deleted)"
  fi
  if [ ! -d repo ]; then
    if [ -f "code_${C8}.tar.gz" ]; then mkdir repo && tar xzf "code_${C8}.tar.gz" -C repo && cat COMMIT > repo/.package_commit && echo "code unpacked to ./repo (commit $(cat COMMIT))"
    else echo "code_${C8}.tar.gz MISSING"; ok=0; fi
  else echo "./repo is the unpacked code of commit $(cat repo/.package_commit)"; fi
fi
if sec networks; then
  echo "== networks (full 2920x3h; registered SHA256)"
  ( cd repo && env -u GRB_LICENSE_FILE "$PY" scripts_project/b4_batch4.py base-check --nets "$HERE/networks" --out "$HERE/PREFLIGHT_BASE_CHECK${PREFLIGHT_TAG:+_$PREFLIGHT_TAG}.json" ) || { echo "BASE NETWORK SHA256 / BYTES DIFFER FROM THE BUILD RECEIPTS OR THE REGISTERED VALUES"; ok=0; }   # PREFLIGHT_TAG (HPR): per-job file names when two jobs share the package folder
  for f in integrated_costs_active_research.csv disconnected_costs_active_research.csv; do [ -s "networks/$f" ] || { echo "networks/$f MISSING"; ok=0; }; done
  ls networks/*_365_24h_* > /dev/null 2>&1 && { echo "365x24h network found in the package (not part of the fourth batch)"; ok=0; } || echo "no 365x24h network in the package (as registered)"
fi
if sec env; then
  echo "== environment vs env/ENV_LOCK.txt"
  "$PY" env/env_check.py env/ENV_LOCK.txt --out "$HERE/PREFLIGHT_ENV_CHECK${PREFLIGHT_TAG:+_$PREFLIGHT_TAG}.json" || { echo "KEY PACKAGES DIFFER (do not run the batch)"; ok=0; }
fi
if sec profile; then
  echo "== solver profile"
  ( cd repo && env -u GRB_LICENSE_FILE "$PY" - "$R_TL" <<'P' ) || ok=0
import sys, yaml
sys.path.insert(0, "scripts_project")
from s2_solve import interior_solution, profile_parameters
S = yaml.safe_load(open("configs/research/baseline.yaml"))["research"]["solver"]
par = profile_parameters(S["profiles"], "formal_barrier_1e6_t16", float(sys.argv[1]))
good = interior_solution("gurobi", par) and int(par.get("Threads", 0)) == 16 and float(par["BarConvTol"]) == 1e-6
print("formal_barrier_1e6_t16", S["profiles"]["formal_barrier_1e6_t16"], "| interior-point gate path:", interior_solution("gurobi", par), "| Threads", par.get("Threads"), "| TimeLimit", par["TimeLimit"], "OK" if good else "UNEXPECTED")
sys.exit(0 if good else 1)
P
fi
if sec code; then
  echo "== code imports (no licence)"
  ( cd repo && env -u GRB_LICENSE_FILE "$PY" - "$R_TL" <<'P' ) || { echo "IMPORT FAILED"; ok=0; }
import sys
sys.path.insert(0, "scripts_project"); sys.path.insert(0, "scripts_project/v5")
import s2_solve, b4_split_solve, b4_batch4, l23_violation_analysis, s4o_c1_precision, m12_allocation, m12_rhs_audit, gates_v6
assert list(b4_batch4.RUNS) == ["F1", "F2"], "run table"
assert "--split-stage" in open("scripts_project/s2_solve.py").read() and hasattr(s2_solve, "post_solve") and hasattr(s2_solve, "assign_split_result"), "split / post_solve code"
# HPR (RUN_PLAN_HPC section 10): the registered limits of b4_batch4.py equal the R_* constants of run_batch4.sh next to this preflight and this preflight's R_TL
import re
src = open("../run_batch4.sh").read(); m = re.search(r"^R_TL=(\d+); R_WALL=(\d+); R_GAP=(\d+); R_MODE=(\w+)", src, re.M)
assert m and (int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)) == (b4_batch4.TIME_LIMIT_S, b4_batch4.WALL_CAP_S, b4_batch4.LICENCE_GAP_S, "split"), ("run_batch4.sh R_* differ from b4_batch4.py", m and m.groups())
assert b4_batch4.TIME_LIMIT_S == int(sys.argv[1]), "preflight R_TL differs from b4_batch4.py TIME_LIMIT_S"
assert b4_batch4.BUILD_COMMIT.startswith("72083fde") and set(b4_batch4.REGISTERED_SHA) == {"integrated_2920_3h_unsolved.nc", "disconnected_2920_3h_unsolved.nc"}, "registered networks"
print("modules import; run table", ", ".join(b4_batch4.RUNS), "| thresholds memory", b4_batch4.MEMORY_STOP_FRACTION, "projection", b4_batch4.PROJECTION_FRACTION, "P1", b4_batch4.P1_THRESHOLD, b4_batch4.P1_MIN_CORES, b4_batch4.P1_WINDOW_S,
      "| registered TimeLimit", b4_batch4.TIME_LIMIT_S, "wall cap", b4_batch4.WALL_CAP_S, "gap", b4_batch4.LICENCE_GAP_S, "= run_batch4.sh R_TL / R_WALL / R_GAP; build commit", b4_batch4.BUILD_COMMIT[:8])
P
fi
if sec tools; then
  echo "== tools"
  if [ -x /usr/bin/time ] && /usr/bin/time -v true > /dev/null 2>&1; then echo "/usr/bin/time (GNU time -v) present"; else echo "MISSING /usr/bin/time (apt-get install -y time)"; ok=0; fi
  if command -v setsid >/dev/null 2>&1 && setsid true >/dev/null 2>&1; then echo "setsid present"; else echo "MISSING setsid (apt-get install -y util-linux)"; ok=0; fi
  command -v pgrep >/dev/null 2>&1 && echo "pgrep present" || { echo "MISSING pgrep (apt-get install -y procps)"; ok=0; }
  command -v timeout >/dev/null 2>&1 && timeout 5 true && echo "timeout present" || { echo "MISSING timeout (coreutils)"; ok=0; }
  command -v tmux >/dev/null 2>&1 && echo "tmux present" || echo "WARNING: tmux missing - run run_batch4.sh in a detached session (apt-get install -y tmux)"
fi
if sec licence; then
  echo "== licence (output suppressed)"
  if [ -z "${GRB_LICENSE_FILE:-}" ] || [ ! -r "$GRB_LICENSE_FILE" ]; then echo "GRB_LICENSE_FILE not set or not readable"; ok=0
  else
    "$PY" -c "import gurobipy as gp; m = gp.Model(); m.dispose()" > /dev/null 2>&1 && echo "Gurobi accepts the licence (output suppressed); one WLS token is held >= 5 min (run_batch4.sh waits 330 s)" \
      || { echo "Gurobi licence check FAILED (repeat the command by hand to see the message; never share licence lines)"; ok=0; }
  fi
fi
if sec resources; then
  echo "== resources (container cgroup quota; host values only as fallback)"
  host_cores=$(nproc); host_mem=$(awk '/MemTotal/ {printf "%.0f", $2/1048576}' /proc/meminfo); cores=""; csrc=""; lim=""; msrc=""
  if [ -r "$CGROUP_ROOT/cpu.max" ]; then read -r q p < "$CGROUP_ROOT/cpu.max"
    if [ "$q" != max ] && [ "${p:-0}" -gt 0 ] 2>/dev/null; then cores=$(( q / p )); csrc="cgroup v2 cpu.max ($q/$p)"; fi
  elif [ -r "$CGROUP_ROOT/cpu/cpu.cfs_quota_us" ] && [ -r "$CGROUP_ROOT/cpu/cpu.cfs_period_us" ]; then q=$(cat "$CGROUP_ROOT/cpu/cpu.cfs_quota_us"); p=$(cat "$CGROUP_ROOT/cpu/cpu.cfs_period_us")
    if [ "$q" -gt 0 ] 2>/dev/null && [ "$p" -gt 0 ] 2>/dev/null; then cores=$(( q / p )); csrc="cgroup v1 cfs quota ($q/$p)"; fi
  fi
  [ -n "$cores" ] || { cores=$host_cores; csrc="no cgroup CPU quota: host nproc"; }
  if [ -r "$CGROUP_ROOT/memory.max" ]; then lim=$(cat "$CGROUP_ROOT/memory.max"); msrc="cgroup v2 memory.max"
  elif [ -r "$CGROUP_ROOT/memory.limit_in_bytes" ]; then lim=$(cat "$CGROUP_ROOT/memory.limit_in_bytes"); msrc="cgroup v1 job directory memory.limit_in_bytes"   # HPR: a PBS job cgroup directory given as CGROUP_ROOT
  elif [ -r "$CGROUP_ROOT/memory/memory.limit_in_bytes" ]; then lim=$(cat "$CGROUP_ROOT/memory/memory.limit_in_bytes"); msrc="cgroup v1 memory.limit_in_bytes"; fi
  case "$lim" in ""|max) lim="";; *) [ "${#lim}" -ge 19 ] && lim="";; esac
  if [ -n "$lim" ]; then mem=$(( lim / 1073741824 )); else mem=$host_mem; msrc="no cgroup memory limit: host MemTotal"; fi
  DISK_PATH="${PREFLIGHT_DISK_PATH:-$HERE}"
  disk=$(df -Pk "$DISK_PATH" | awk 'NR==2 {printf "%d", $4*1024/1e9}'); disk_gib=$(df -Pk "$DISK_PATH" | awk 'NR==2 {printf "%.0f", $4/1048576}')
  anon=""; for f in "$CGROUP_ROOT/memory.stat" "$CGROUP_ROOT/memory/memory.stat"; do [ -r "$f" ] && { anon=$(awk '$1 == "anon" {a=$2} $1 == "total_rss" {t=$2} $1 == "rss" {r=$2} END {v = (a != "") ? a : ((t != "") ? t : r); if (v != "") printf "%.1f", v/1073741824}' "$f"); break; }; done
  echo "container CPU cores $cores [$csrc]; host nproc $host_cores"
  echo "container memory $mem GiB [$msrc]; anon in use now ${anon:-?} GiB; host MemTotal $host_mem GiB; free disk $disk GB ($disk_gib GiB) under $DISK_PATH"
  echo "need (hard floor, RUN_PLAN_B4.md section 5): cores >= $NEED_CORES, memory >= $NEED_MEM_GIB GiB, free data disk >= $NEED_DISK_GB GB"
  [ "$cores" -ge $NEED_CORES ] && [ "$mem" -ge $NEED_MEM_GIB ] && [ "$disk" -ge $NEED_DISK_GB ] || { echo "RESOURCE CHECK FAILED"; ok=0; }
  [ "$cores" -ge 33 ] && echo "P1 probe: >= 33 cores - F2 may run beside F1 when F1's peak stays within the threshold" || echo "NOTE: $cores cores < 33: F2 runs after F1 whatever the probe shows (pre-registered)"
fi
[ $ok = 1 ] && echo "PREFLIGHT OK" || { echo "PREFLIGHT FAILED"; exit 1; }
