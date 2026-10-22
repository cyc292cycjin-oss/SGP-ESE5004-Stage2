#!/bin/bash
# M10P cloud package preflight (instruction section 4.4), inside the unpacked package folder on the instance; no solve.
#   PY=<environment python> GRB_LICENSE_FILE=<licence path> bash preflight.sh
# Sections (PREFLIGHT_ONLY = comma list to run a subset; default all):
#   sha        SHA256SUMS of every package file; unpacks code_<COMMIT8>.tar.gz to ./repo (an older ./repo of another commit is moved aside, never deleted)
#   networks   base networks against their build receipts (m10_batch3_summary.py base-check), EXPECTED_VARIANTS.json present (7 variants)
#   env        environment against env/ENV_LOCK.txt (env/env_check.py: key packages identical)
#   profile    profiles formal_barrier and formal_barrier_1e6_t16: s2_solve.py key-name check, interior-point gate path, Threads 8 / 16
#   code       the run / post-processing modules import without the licence (s2_solve, l23_violation_analysis, s4o_c1_precision, m12_allocation,
#              m12_rhs_audit, m08a_variants, gates_v6, m10_batch3_summary); the run table has 12 runs
#   tools      GNU time (-v) at /usr/bin/time, setsid, pgrep, tmux (warning only)
#   licence    GRB_LICENSE_FILE readable and accepted by Gurobi - all output suppressed, nothing of the licence printed; this holds one WLS token for
#              >= 5 min (run_batch3.sh waits 330 s before its first solve)
#   resources  container cgroup quota (cores, memory) and free disk: two profile-A sessions need >= 16 cores, R3 | R4 side by side >= 32 cores
#              (otherwise one after the other - reported, not a failure); memory >= 72 GiB (two 365x24h sessions ~15 GiB each + post-processing
#              ~9 GiB; P1 2920x3h may need far more - that is what it measures); free disk >= 50 GiB, warning below 60 GiB (RUN_PLAN.md section 5:
#              ~39 GiB expected - 11 run folders ~2.1 GiB each with the 0.8 GB LP arrays measured locally, P1 ~7 GiB, packs, environment)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
PY="${PY:-python}"; ok=1; CGROUP_ROOT="${CGROUP_ROOT:-/sys/fs/cgroup}"; ONLY="${PREFLIGHT_ONLY:-sha,networks,env,profile,code,tools,licence,resources}"
NEED_CORES=16; NEED_CORES_T16_PAIR=32; NEED_MEM_GIB=72; NEED_DISK_GIB=50; REC_DISK_GIB=60
sec() { case ",$ONLY," in *",$1,"*) return 0;; *) return 1;; esac; }
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
  echo "== networks"
  ( cd repo && env -u GRB_LICENSE_FILE "$PY" scripts_project/m10_batch3_summary.py base-check --nets "$HERE/networks" --out "$HERE/PREFLIGHT_BASE_CHECK.json" ) || { echo "BASE NETWORK SHA256 DIFFERS FROM THE BUILD RECEIPTS"; ok=0; }
  for f in integrated_costs_active_research.csv disconnected_costs_active_research.csv; do [ -s "networks/$f" ] || { echo "networks/$f MISSING"; ok=0; }; done
  n=$("$PY" -c "import json; print(len(json.load(open('EXPECTED_VARIANTS.json'))))" 2>/dev/null || echo 0)
  [ "$n" = 7 ] && echo "EXPECTED_VARIANTS.json: 7 variants (local dry-run SHA256; run_batch3.sh compares the variants it generates)" || { echo "EXPECTED_VARIANTS.json missing or not 7 entries ($n)"; ok=0; }
fi
if sec env; then
  echo "== environment vs env/ENV_LOCK.txt"
  "$PY" env/env_check.py env/ENV_LOCK.txt --out "$HERE/PREFLIGHT_ENV_CHECK.json" || { echo "KEY PACKAGES DIFFER (do not run the batch)"; ok=0; }
fi
if sec profile; then
  echo "== solver profiles"
  ( cd repo && env -u GRB_LICENSE_FILE "$PY" - <<'P' ) || ok=0
import sys, yaml
sys.path.insert(0, "scripts_project")
from s2_solve import interior_solution, profile_parameters
S = yaml.safe_load(open("configs/research/baseline.yaml"))["research"]["solver"]
bad = 0
for p, threads in (("formal_barrier", 8), ("formal_barrier_1e6_t16", 16)):
    par = profile_parameters(S["profiles"], p, 21600)   # refuses parameter names that differ from the code convention only by case
    good = interior_solution("gurobi", par) and int(par.get("Threads", 0)) == threads
    bad += not good
    print(p, S["profiles"][p], "| interior-point gate path:", interior_solution("gurobi", par), "| Threads", par.get("Threads"), "OK" if good else "UNEXPECTED")
print("default profile:", S["profile"], "| run_rules profile_chain:", S["run_rules"]["profile_chain"]["candidate"], "vs", S["run_rules"]["profile_chain"]["reference"])
sys.exit(1 if bad else 0)
P
fi
if sec code; then
  echo "== code imports (no licence)"
  ( cd repo && env -u GRB_LICENSE_FILE "$PY" - <<'P' ) || { echo "IMPORT FAILED"; ok=0; }
import sys
sys.path.insert(0, "scripts_project"); sys.path.insert(0, "scripts_project/v5")
import s2_solve, l23_violation_analysis, s4o_c1_precision, m12_allocation, m12_rhs_audit, m08a_variants, gates_v6, m10_batch3_summary
assert len(m10_batch3_summary.RUNS) == 12, "run table"
print("modules import; run table", ", ".join(m10_batch3_summary.RUNS))
P
fi
if sec tools; then
  echo "== tools"
  if [ -x /usr/bin/time ] && /usr/bin/time -v true > /dev/null 2>&1; then echo "/usr/bin/time (GNU time -v) present"; else echo "MISSING /usr/bin/time (apt-get install -y time)"; ok=0; fi
  if command -v setsid >/dev/null 2>&1 && setsid true >/dev/null 2>&1; then echo "setsid present"; else echo "MISSING setsid (apt-get install -y util-linux)"; ok=0; fi
  command -v pgrep >/dev/null 2>&1 && echo "pgrep present" || { echo "MISSING pgrep (apt-get install -y procps)"; ok=0; }
  command -v tmux >/dev/null 2>&1 && echo "tmux present" || echo "WARNING: tmux missing - run run_batch3.sh in a detached session (apt-get install -y tmux)"
fi
if sec licence; then
  echo "== licence (output suppressed)"
  if [ -z "${GRB_LICENSE_FILE:-}" ] || [ ! -r "$GRB_LICENSE_FILE" ]; then echo "GRB_LICENSE_FILE not set or not readable"; ok=0
  else
    "$PY" -c "import gurobipy as gp; m = gp.Model(); m.dispose()" > /dev/null 2>&1 && echo "Gurobi accepts the licence (output suppressed); one WLS token is held >= 5 min (run_batch3.sh waits 330 s)" \
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
  disk=$(df -Pk "$HERE" | awk 'NR==2 {printf "%.0f", $4/1048576}')
  echo "container CPU cores $cores [$csrc]; host nproc $host_cores"
  echo "container memory $mem GiB [$msrc]; host MemTotal $host_mem GiB; free disk $disk GiB under $HERE"
  echo "need: cores >= $NEED_CORES (two profile-A sessions), memory >= $NEED_MEM_GIB GiB, free disk >= $NEED_DISK_GIB GiB"
  [ "$cores" -ge $NEED_CORES ] && [ "$mem" -ge $NEED_MEM_GIB ] && [ "$disk" -ge $NEED_DISK_GIB ] || { echo "RESOURCE CHECK FAILED"; ok=0; }
  [ "$disk" -ge $REC_DISK_GIB ] || echo "WARNING: free disk below the recommended $REC_DISK_GIB GiB (expected use ~39 GiB; not a failure)"
  [ "$cores" -ge $NEED_CORES_T16_PAIR ] && echo "R3 | R4 (Threads 16 + 16) will run side by side" || echo "NOTE: $cores cores < 32: R3 and R4 (Threads 16 each) will run one after the other (pre-registered rule)"
fi
[ $ok = 1 ] && echo "PREFLIGHT OK" || { echo "PREFLIGHT FAILED"; exit 1; }
