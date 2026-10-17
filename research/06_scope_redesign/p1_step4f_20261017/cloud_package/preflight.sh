#!/bin/bash
# S4F cloud package preflight (on the cloud instance, inside the unpacked package folder; no solve):
#   GRB_LICENSE_FILE=/path/to/gurobi.lic PY=/root/miniforge3/envs/pypsa-earth/bin/python bash preflight.sh [serial|lanes2|lanes3] [solver_profile]
# Checks: SHA256SUMS, unpacks the code snapshot to ./repo, package versions, licence file readable and accepted by Gurobi (output suppressed,
# no licence content printed), CPU / memory / disk against the S4F resource estimate (CLOUD_RESOURCE_ESTIMATE.md section 15), the four
# networks, and (optional second argument) that the solver profile to be passed to run_365x24h.sh exists in the packaged configuration.
set -u
MODE=${1:-serial}; PROFILE=${2:-}
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
PY="${PY:-python}"; ok=1
case "$MODE" in serial|lanes2|lanes3) ;; *) echo "mode serial|lanes2|lanes3"; exit 2;; esac
echo "== SHA256SUMS"; sha256sum -c --quiet SHA256SUMS && echo "all files OK" || { echo "CHECKSUM MISMATCH"; ok=0; }
if [ ! -d repo ]; then mkdir repo && tar xzf code_*.tar.gz -C repo && echo "code unpacked to ./repo (commit $(cat COMMIT))"; fi
echo "== networks"
for f in integrated_365_24h_unsolved.nc disconnected_365_24h_unsolved.nc integrated_nze_365_24h_unsolved.nc disconnected_gap_diagnostic_365_24h_unsolved.nc; do
  [ -s "networks/$f" ] && echo "networks/$f present" || { echo "networks/$f MISSING"; ok=0; }
done
echo "== solver profile"
if [ -z "$PROFILE" ]; then echo "no profile given: run_365x24h.sh will refuse to start until --solver-profile is supplied (user-confirmed profile A: formal_barrier)"
else
  "$PY" - "$PROFILE" <<'P' || ok=0
import sys, yaml
p = sys.argv[1]; prof = yaml.safe_load(open("repo/configs/research/baseline.yaml"))["research"]["solver"]["profiles"]
print(p, prof[p]) if p in prof else (print("UNKNOWN PROFILE", p, "- available:", sorted(prof)), sys.exit(1))
P
fi
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
echo "== licence"
if [ -z "${GRB_LICENSE_FILE:-}" ] || [ ! -r "$GRB_LICENSE_FILE" ]; then echo "GRB_LICENSE_FILE not set or not readable"; ok=0
else
  "$PY" -c "import gurobipy as gp; m = gp.Model(); m.dispose()" > /dev/null 2>&1 && echo "Gurobi licence accepted (output suppressed)" || { echo "Gurobi licence check FAILED (run the same command manually to see the message; do not share licence lines)"; ok=0; }
fi
echo "== resources"
cores=$(nproc); mem=$(awk '/MemTotal/ {printf "%.0f", $2/1048576}' /proc/meminfo); disk=$(df -Pk "$HERE" | awk 'NR==2 {printf "%.0f", $4/1048576}')
# CLOUD_RESOURCE_ESTIMATE.md section 15: lower bound / recommended per mode (one run at a time / two lanes / three lanes)
case "$MODE" in serial) need_c=8; need_m=36; need_d=35; rec_m=48;; lanes2) need_c=16; need_m=72; need_d=45; rec_m=96;; lanes3) need_c=24; need_m=104; need_d=50; rec_m=128;; esac
echo "cores $cores (need >= $need_c), memory ${mem} GiB (need >= $need_m), free disk ${disk} GiB (need >= $need_d) for mode $MODE"
[ "$cores" -ge $need_c ] && [ "$mem" -ge $need_m ] && [ "$disk" -ge $need_d ] || { echo "RESOURCE CHECK FAILED"; ok=0; }
[ "$mem" -ge $rec_m ] || echo "WARNING: memory below the recommended ${rec_m} GiB for mode $MODE (upper peak estimate leaves little margin; not a failure)"
[ $ok = 1 ] && echo "PREFLIGHT OK" || { echo "PREFLIGHT FAILED"; exit 1; }
