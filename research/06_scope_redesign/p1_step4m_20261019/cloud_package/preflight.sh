#!/bin/bash
# S4M cloud package preflight (S4M-3): the S4L preflight unchanged (container cgroup quota, setsid check); the resource bounds refer to CLOUD_RESOURCE_ESTIMATE.md sections 20-22.
# S4L cloud package preflight (S4L-3, decision 112 c; successor of the S4K preflight of package code 56d28358 - not yet packaged). On the cloud
# instance, inside the unpacked package folder; no solve:
#   GRB_LICENSE_FILE=/path/to/gurobi.lic PY=/root/miniconda3/envs/pypsa-earth/bin/python bash preflight.sh [serial|lanes2] [solver_profile]
# Checks: SHA256SUMS, unpacks the code snapshot to ./repo, package versions, GNU time at /usr/bin/time and setsid (run_365x24h.sh needs both;
# S4I U3, decision 106 b), licence file readable and accepted by Gurobi (output suppressed, no licence content printed; this check holds one WLS
# token for >= 5 min, run_365x24h.sh --mode lanes2 waits for it), CPU / memory / disk against the resource estimate (CLOUD_RESOURCE_ESTIMATE.md
# sections 20-21), the four networks, and (optional second argument) that the solver profile exists in the packaged configuration.
# Change against the S4K preflight (L23 finding 1): CPU cores and memory are the CONTAINER cgroup quota, not the host nproc / /proc/meminfo
# (on the L23 instance the host showed 48 threads / 440 GB while the container had 12 cores / 90 GiB): cgroup v2 cpu.max + memory.max, cgroup v1
# cpu/cpu.cfs_quota_us + cpu/cpu.cfs_period_us + memory/memory.limit_in_bytes; an unlimited quota falls back to nproc / MemTotal and says so.
# lanes3 is withdrawn (S4I K2, decision 106 a: the academic WLS licence allows at most 2 concurrent sessions).
# Test hooks (defaults are the production values): CGROUP_ROOT (/sys/fs/cgroup); PREFLIGHT_ONLY = comma list of sections to run
# (sha,networks,profile,versions,tools,licence,resources; default all).
set -u
MODE=${1:-serial}; PROFILE=${2:-}
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
PY="${PY:-python}"; ok=1; CGROUP_ROOT="${CGROUP_ROOT:-/sys/fs/cgroup}"; ONLY="${PREFLIGHT_ONLY:-sha,networks,profile,versions,tools,licence,resources}"
sec() { case ",$ONLY," in *",$1,"*) return 0;; *) return 1;; esac; }
case "$MODE" in
  serial|lanes2) ;;
  lanes3) echo "mode lanes3 is withdrawn (academic WLS licence: at most 2 concurrent sessions); use serial (recommended) or lanes2"; exit 2;;
  *) echo "mode serial|lanes2"; exit 2;;
esac
if sec sha; then
  echo "== SHA256SUMS"; sha256sum -c --quiet SHA256SUMS && echo "all files OK" || { echo "CHECKSUM MISMATCH"; ok=0; }
  if [ ! -d repo ]; then mkdir repo && tar xzf code_*.tar.gz -C repo && echo "code unpacked to ./repo (commit $(cat COMMIT))"; fi
fi
if sec networks; then
  echo "== networks"
  for f in integrated_365_24h_unsolved.nc disconnected_365_24h_unsolved.nc integrated_nze_365_24h_unsolved.nc disconnected_gap_diagnostic_365_24h_unsolved.nc; do
    [ -s "networks/$f" ] && echo "networks/$f present" || { echo "networks/$f MISSING"; ok=0; }
  done
fi
if sec profile; then
  echo "== solver profile"
  if [ -z "$PROFILE" ]; then echo "no profile given: run_365x24h.sh will refuse to start until --solver-profile is supplied (first batch: formal_barrier, profile A)"
  else
    "$PY" - "$PROFILE" <<'P' || ok=0
import sys, yaml
p = sys.argv[1]; prof = yaml.safe_load(open("repo/configs/research/baseline.yaml"))["research"]["solver"]["profiles"]
print(p, prof[p]) if p in prof else (print("UNKNOWN PROFILE", p, "- available:", sorted(prof)), sys.exit(1))
P
  fi
fi
if sec versions; then
  echo "== versions"
  "$PY" - <<'P' || ok=0
import sys, importlib
want = dict(pypsa="0.30.3", linopy="0.5.5", gurobipy="12.0.3", numpy="1.26.4")
bad = []
print("python", sys.version.split()[0]); bad += [] if sys.version.split()[0] == "3.11.13" else ["python"]
for m, v in want.items():
    mod = importlib.import_module(m); got = getattr(mod, "__version__", None) or ".".join(map(str, mod.gurobi.version()))
    print(m, got); bad += [] if got == v else [m]
sys.exit(1 if bad else 0)
P
fi
if sec tools; then
  echo "== tools"
  if [ -x /usr/bin/time ] && /usr/bin/time -v true > /dev/null 2>&1; then echo "/usr/bin/time (GNU time, -v) present"
  else echo "MISSING /usr/bin/time (GNU time with -v): run_365x24h.sh would fail every run within seconds. Install: apt-get install -y time"; ok=0; fi
  if command -v setsid >/dev/null 2>&1 && setsid true >/dev/null 2>&1; then echo "setsid (util-linux) present: each solve gets its own process group (wall-clock kill of the whole group)"
  else echo "MISSING setsid (util-linux): run_365x24h.sh refuses to start. Install: apt-get install -y util-linux"; ok=0; fi
fi
if sec licence; then
  echo "== licence"
  if [ -z "${GRB_LICENSE_FILE:-}" ] || [ ! -r "$GRB_LICENSE_FILE" ]; then echo "GRB_LICENSE_FILE not set or not readable"; ok=0
  else
    "$PY" -c "import gurobipy as gp; m = gp.Model(); m.dispose()" > /dev/null 2>&1 && echo "Gurobi licence accepted (output suppressed); this check keeps one WLS token for >= 5 min (lanes2 waits 330 s at start)" || { echo "Gurobi licence check FAILED (run the same command manually to see the message; do not share licence lines)"; ok=0; }
  fi
fi
if sec resources; then
  echo "== resources (container cgroup quota; host values only as fallback)"
  host_cores=$(nproc); host_mem=$(awk '/MemTotal/ {printf "%.0f", $2/1048576}' /proc/meminfo)
  cores=""; cores_src=""; mem=""; mem_src=""
  if [ -r "$CGROUP_ROOT/cpu.max" ]; then                       # cgroup v2: "<quota> <period>" or "max <period>"
    read -r q p < "$CGROUP_ROOT/cpu.max"
    if [ "$q" != "max" ] && [ -n "${p:-}" ] && [ "$p" -gt 0 ] 2>/dev/null; then cores=$(awk -v q="$q" -v p="$p" 'BEGIN {printf "%d", q/p}'); cores_src="cgroup v2 cpu.max ($q/$p)"; fi
  elif [ -r "$CGROUP_ROOT/cpu/cpu.cfs_quota_us" ] && [ -r "$CGROUP_ROOT/cpu/cpu.cfs_period_us" ]; then   # cgroup v1: quota -1 = unlimited
    q=$(cat "$CGROUP_ROOT/cpu/cpu.cfs_quota_us"); p=$(cat "$CGROUP_ROOT/cpu/cpu.cfs_period_us")
    if [ "$q" -gt 0 ] 2>/dev/null && [ "$p" -gt 0 ] 2>/dev/null; then cores=$(awk -v q="$q" -v p="$p" 'BEGIN {printf "%d", q/p}'); cores_src="cgroup v1 cpu.cfs_quota_us/cpu.cfs_period_us ($q/$p)"; fi
  fi
  [ -n "$cores" ] || { cores=$host_cores; cores_src="no cgroup CPU quota (unlimited or absent): host nproc"; }
  lim=""
  if [ -r "$CGROUP_ROOT/memory.max" ]; then lim=$(cat "$CGROUP_ROOT/memory.max"); mem_src="cgroup v2 memory.max"
  elif [ -r "$CGROUP_ROOT/memory/memory.limit_in_bytes" ]; then lim=$(cat "$CGROUP_ROOT/memory/memory.limit_in_bytes"); mem_src="cgroup v1 memory.limit_in_bytes"; fi
  case "$lim" in ""|max) lim="";; *) [ "${#lim}" -ge 19 ] && lim="";; esac   # v1 "unlimited" is 9223372036854771712 (19 digits)
  if [ -n "$lim" ]; then mem=$(awk -v b="$lim" 'BEGIN {printf "%.0f", b/1073741824}'); else mem=$host_mem; mem_src="no cgroup memory limit (unlimited or absent): host MemTotal"; fi
  disk=$(df -Pk "$HERE" | awk 'NR==2 {printf "%.0f", $4/1048576}')
  echo "container CPU cores $cores [$cores_src]; host nproc $host_cores"
  echo "container memory ${mem} GiB [$mem_src]; host MemTotal ${host_mem} GiB"
  # CLOUD_RESOURCE_ESTIMATE.md sections 20-21: lower bound / recommended per mode (one run at a time / two lanes)
  # serial memory minimum 40 GiB (user decision 2026-10-18 on S4K report section 8 item 1); L23 measured peaks 13.8-15.3 GiB per run (section 21)
  case "$MODE" in serial) need_c=8; need_m=40; need_d=35; rec_m=48;; lanes2) need_c=16; need_m=72; need_d=45; rec_m=96;; esac
  echo "cores $cores (need >= $need_c), memory ${mem} GiB (need >= $need_m), free disk ${disk} GiB (need >= $need_d) for mode $MODE"
  [ "$cores" -ge $need_c ] && [ "$mem" -ge $need_m ] && [ "$disk" -ge $need_d ] || { echo "RESOURCE CHECK FAILED"; ok=0; }
  [ "$mem" -ge $rec_m ] || echo "WARNING: memory below the recommended ${rec_m} GiB for mode $MODE (upper peak estimate leaves little margin; not a failure)"
fi
[ $ok = 1 ] && echo "PREFLIGHT OK" || { echo "PREFLIGHT FAILED"; exit 1; }
