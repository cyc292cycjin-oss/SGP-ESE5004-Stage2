#!/bin/bash
# DFX package preflight (RUN_PLAN_DFX.md section 5; derived from the B4P preflight.sh), inside the unpacked package folder on the instance; no solve.
#   PY=<environment python> GRB_LICENSE_FILE=<licence path> bash preflight_dfx.sh
# Sections (PREFLIGHT_ONLY = comma list; default all):
#   guards     none of the test hooks / dry-run switches of run_dfx.sh is set in this shell (M10A B5.5)
#   sha        SHA256SUMS of every package file; unpacks code_<COMMIT8>.tar.gz to ./repo (an older ./repo of another commit is moved aside)
#   networks   the two 365x24h v2 networks against their build receipts AND the registered SHA256 / bytes (dfx_batch.py base-check); no 2920x3h file
#   env        environment against env/ENV_LOCK.txt (env/env_check.py: key packages identical with the third-batch cloud environment)
#   profile    profile formal_barrier_1e6_t16: s2_solve.py key-name check, interior-point gate path, Threads 16, BarConvTol 1e-6; TimeLimit = the
#              registered per-run values (dfx_batch.py: V1 21,600 s, V2 10,800 s; user amendment 2026-10-27)
#   code       the run / post-processing modules import without the licence (s2_solve, dfx_batch, m10_batch3_summary, l23_violation_analysis,
#              s4o_c1_precision, m12_allocation, m12_rhs_audit, gates_v6); the run table is V1, V2; the registered limits; s2_solve has post_solve
#   tools      GNU time (-v) at /usr/bin/time, setsid, pgrep, timeout, tmux (warning only)
#   licence    GRB_LICENSE_FILE readable and accepted by Gurobi - output suppressed, nothing printed; holds one WLS token >= 5 min (330 s gap)
#   resources  container cgroup quota (cores, memory), free data disk under this folder (PREFLIGHT_DISK_PATH override) against the HARD FLOOR of
#              RUN_PLAN_DFX.md section 5: cores >= NEED_CORES (17), memory >= NEED_MEM_GIB (64), free disk >= NEED_DISK_GB (45); >= 33 cores -> V1 | V2 in parallel
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
PY="${PY:-python}"; ok=1; CGROUP_ROOT="${CGROUP_ROOT:-/sys/fs/cgroup}"; ONLY="${PREFLIGHT_ONLY:-guards,sha,networks,env,profile,code,tools,licence,resources}"
NEED_CORES=${NEED_CORES:-17}; NEED_MEM_GIB=${NEED_MEM_GIB:-64}; NEED_DISK_GB=${NEED_DISK_GB:-45}; PAR_CORES=33   # hard floor (RUN_PLAN_DFX section 5: third-batch T16 peaks 22.8 / 19.3 GiB + post-processing ~11 GiB, x2 margin; disk as the third batch)
sec() { case ",$ONLY," in *",$1,"*) return 0;; *) return 1;; esac; }
if sec guards; then
  echo "== guards: test hooks / dry-run switches in this shell"; bad=()
  for k in ALLOW_UNREGISTERED BUILD_ONLY POST_ONLY DRY TRUNCATE SOLVE_CMD VA_CMD C1_CMD M12_CMD M12A_CMD G6_CMD SUM_CMD PACK_CMD WALL_CAP_S GUROBI_TIME_LIMIT_S LICENCE_GAP_S GRACE_S MONITOR_S POST_TIMEOUT_S PACK_TIMEOUT_S $(compgen -A variable | grep -E '^FAKE_'); do
    [ -z "${!k:-}" ] || bad+=("$k")
  done
  if [ ${#bad[@]} -gt 0 ]; then echo "SET IN THIS SHELL - unset before the formal run: ${bad[*]}"; ok=0; else echo "no test hook / dry-run switch set"; fi
  for k in RUN_DIR CORES REPO NETS CGROUP_ROOT TMPDIR PREFLIGHT_DISK_PATH; do [ -z "${!k:-}" ] || echo "NOTE: $k=${!k} (operational override; make sure it is intended)"; done
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
  echo "== networks (365x24h v2; build receipts + registered SHA256 / bytes)"
  ( cd repo && env -u GRB_LICENSE_FILE "$PY" scripts_project/dfx_batch.py base-check --nets "$HERE/networks" --out "$HERE/PREFLIGHT_BASE_CHECK.json" ) || { echo "BASE NETWORK SHA256 / BYTES DIFFER FROM THE BUILD RECEIPTS OR THE REGISTERED VALUES (or a 2920x3h file is present)"; ok=0; }
  for f in integrated_costs_active_research.csv disconnected_costs_active_research.csv; do [ -s "networks/$f" ] || { echo "networks/$f MISSING"; ok=0; }; done
  ls networks/*_2920_3h_* > /dev/null 2>&1 && { echo "2920x3h network found in the package (not part of the DFX 365x24h screening)"; ok=0; } || echo "no 2920x3h network in the package (as registered)"
fi
if sec env; then
  echo "== environment vs env/ENV_LOCK.txt"
  "$PY" env/env_check.py env/ENV_LOCK.txt --out "$HERE/PREFLIGHT_ENV_CHECK.json" || { echo "KEY PACKAGES DIFFER (do not run the batch)"; ok=0; }
fi
if sec profile; then
  echo "== solver profile"
  ( cd repo && env -u GRB_LICENSE_FILE "$PY" - <<'P' ) || ok=0
import sys, yaml
sys.path.insert(0, "scripts_project")
from s2_solve import interior_solution, profile_parameters
from dfx_batch import TIME_LIMIT_S, T16
S = yaml.safe_load(open("configs/research/baseline.yaml"))["research"]["solver"]
good = True
for rid, tl in TIME_LIMIT_S.items():
    par = profile_parameters(S["profiles"], T16, float(tl))
    ok = interior_solution("gurobi", par) and int(par.get("Threads", 0)) == 16 and float(par["BarConvTol"]) == 1e-6 and float(par["TimeLimit"]) == float(tl)
    good = good and ok
    print(rid, T16, "| interior-point gate path:", interior_solution("gurobi", par), "| Threads", par.get("Threads"), "| BarConvTol", par.get("BarConvTol"), "| TimeLimit", par["TimeLimit"], "OK" if ok else "UNEXPECTED")
print("profile", S["profiles"][T16])
sys.exit(0 if good else 1)
P
fi
if sec code; then
  echo "== code imports (no licence)"
  ( cd repo && env -u GRB_LICENSE_FILE "$PY" - <<'P' ) || { echo "IMPORT FAILED"; ok=0; }
import sys
sys.path.insert(0, "scripts_project"); sys.path.insert(0, "scripts_project/v5")
import s2_solve, dfx_batch, m10_batch3_summary, l23_violation_analysis, s4o_c1_precision, m12_allocation, m12_rhs_audit, gates_v6
assert list(dfx_batch.RUNS) == ["V1", "V2"], "run table"
assert dfx_batch.TIME_LIMIT_S == {"V1": 21600, "V2": 10800} and dfx_batch.WALL_MARGIN_S == 1200 and dfx_batch.LICENCE_GAP_S == 330 and dfx_batch.PARALLEL_MIN_CORES == 33, "registered limits"
assert dfx_batch.SCHEDULE == [("1", ["V1"], ["V2"])] and dfx_batch.STOP_ALWAYS == ("V1", "V2"), "schedule / stop rule"
assert hasattr(s2_solve, "post_solve") and "--stop-before-solve" in open("scripts_project/s2_solve.py").read(), "post_solve / dry-run code"
print("modules import; run table", ", ".join(dfx_batch.RUNS), "| limits", dfx_batch.TIME_LIMIT_S, "+", dfx_batch.WALL_MARGIN_S, "s wall margin | gap", dfx_batch.LICENCE_GAP_S, "s | parallel >=", dfx_batch.PARALLEL_MIN_CORES, "cores")
P
fi
if sec tools; then
  echo "== tools"
  if [ -x /usr/bin/time ] && /usr/bin/time -v true > /dev/null 2>&1; then echo "/usr/bin/time (GNU time -v) present"; else echo "MISSING /usr/bin/time (apt-get install -y time)"; ok=0; fi
  if command -v setsid >/dev/null 2>&1 && setsid true >/dev/null 2>&1; then echo "setsid present"; else echo "MISSING setsid (apt-get install -y util-linux)"; ok=0; fi
  command -v pgrep >/dev/null 2>&1 && echo "pgrep present" || { echo "MISSING pgrep (apt-get install -y procps)"; ok=0; }
  command -v timeout >/dev/null 2>&1 && timeout 5 true && echo "timeout present" || { echo "MISSING timeout (coreutils)"; ok=0; }
  command -v tmux >/dev/null 2>&1 && echo "tmux present" || echo "WARNING: tmux missing - run run_dfx.sh in a detached session (apt-get install -y tmux)"
fi
if sec licence; then
  echo "== licence (output suppressed)"
  if [ -z "${GRB_LICENSE_FILE:-}" ] || [ ! -r "$GRB_LICENSE_FILE" ]; then echo "GRB_LICENSE_FILE not set or not readable"; ok=0
  else
    "$PY" -c "import gurobipy as gp; m = gp.Model(); m.dispose()" > /dev/null 2>&1 && echo "Gurobi accepts the licence (output suppressed); one WLS token is held >= 5 min (run_dfx.sh waits 330 s)" \
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
  elif [ -r "$CGROUP_ROOT/memory/memory.limit_in_bytes" ]; then lim=$(cat "$CGROUP_ROOT/memory/memory.limit_in_bytes"); msrc="cgroup v1 memory.limit_in_bytes"; fi
  case "$lim" in ""|max) lim="";; *) [ "${#lim}" -ge 19 ] && lim="";; esac
  if [ -n "$lim" ]; then mem=$(( lim / 1073741824 )); else mem=$host_mem; msrc="no cgroup memory limit: host MemTotal"; fi
  DISK_PATH="${PREFLIGHT_DISK_PATH:-$HERE}"
  disk=$(df -Pk "$DISK_PATH" | awk 'NR==2 {printf "%d", $4*1024/1e9}'); disk_gib=$(df -Pk "$DISK_PATH" | awk 'NR==2 {printf "%.0f", $4/1048576}')
  anon=$(awk '$1 == "anon" {printf "%.1f", $2/1073741824}' "$CGROUP_ROOT/memory.stat" 2>/dev/null)
  echo "container CPU cores $cores [$csrc]; host nproc $host_cores"
  echo "container memory $mem GiB [$msrc]; anon in use now ${anon:-?} GiB; host MemTotal $host_mem GiB; free disk $disk GB ($disk_gib GiB) under $DISK_PATH"
  echo "need (hard floor, RUN_PLAN_DFX.md section 5): cores >= $NEED_CORES, memory >= $NEED_MEM_GIB GiB, free data disk >= $NEED_DISK_GB GB"
  [ "$cores" -ge $NEED_CORES ] && [ "$mem" -ge $NEED_MEM_GIB ] && [ "$disk" -ge $NEED_DISK_GB ] || { echo "RESOURCE CHECK FAILED"; ok=0; }
  [ "$cores" -ge $PAR_CORES ] && echo ">= $PAR_CORES cores: V1 and V2 run side by side (two WLS sessions)" || echo "NOTE: $cores cores < $PAR_CORES: V2 runs after V1 in one lane (pre-registered)"
fi
[ $ok = 1 ] && echo "PREFLIGHT OK" || { echo "PREFLIGHT FAILED"; exit 1; }
