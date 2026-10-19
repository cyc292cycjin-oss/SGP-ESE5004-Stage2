#!/bin/bash
# S4M speed probe (S4M-3 point 3, decision 116): ONE 56x3h solve of the packaged integrated STEPS probe network with profile A (formal_barrier) on the
# instance, 30 min stop-loss, no retry; then the Gurobi seconds per work unit and per barrier iteration are compared with the SAME run made locally
# (S4M-2 smoke, PROBE_REFERENCE.json in the package) -> speed ratio of the instance and the suggested TimeLimit / wall-clock cap for the pilot.
# PREPARED ONLY - the probe runs on the cloud instance only after the user has authorised it separately (it is a Gurobi solve and holds one WLS
# token for >= 5 min: wait >= 5 min after the probe before the pilot / batch).
#
#   GRB_LICENSE_FILE=/path/to/gurobi.lic PY=<env>/bin/python bash speed_probe.sh [--auth "text"]
#
# Reads: networks/integrated_56_3h_probe_unsolved.nc (the first 56 snapshots of the 2920x3h integrated STEPS network of this package; the LP is the
# one of the local S4M-2 integrated smoke), PROBE_REFERENCE.json (local reference: barrier seconds, iterations, work units, objective, CPU model).
# Writes: probe/<timestamp>/ with the solve outputs, SPEED_PROBE.json (ratios and suggestions), a scrubbed Gurobi log; prints the summary.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
AUTH=""; while [ $# -gt 0 ]; do case "$1" in --auth) AUTH="$2"; shift 2;; *) echo "unknown argument $1"; exit 2;; esac; done
: "${GRB_LICENSE_FILE:?set GRB_LICENSE_FILE to the licence path provided by the user}"
[ -r "$GRB_LICENSE_FILE" ] || { echo "GRB_LICENSE_FILE is not readable"; exit 2; }
PY="${PY:-python}"; REPO="$HERE/repo"; NET="$HERE/networks/integrated_56_3h_probe_unsolved.nc"; REF="$HERE/PROBE_REFERENCE.json"
[ -d "$REPO" ] || { echo "run preflight.sh first (unpacks the code snapshot to ./repo)"; exit 2; }
[ -f "$NET" ] && [ -f "$REF" ] || { echo "probe network or PROBE_REFERENCE.json missing from the package"; exit 2; }
[ -n "$AUTH" ] || AUTH="S4M speed probe (user authorisation text to be supplied with --auth)"
OUT="$HERE/probe/$(date -u +%Y%m%dT%H%M%SZ)_$$"; mkdir -p "$OUT"; ST="$OUT/STATUS.txt"
export PYTHONHASHSEED=0
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(cat "$HERE/COMMIT" 2>/dev/null) cpu:$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')" >> "$ST"
( cd "$REPO" && exec setsid /usr/bin/time -v "$PY" "$REPO/scripts_project/s2_solve.py" --repo "$REPO" --network "$NET" --scenario integrated --output "$OUT/solve" --truncate 56 \
    --label SMOKE_TEST_ONLY --authorization "$AUTH; speed probe" --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 1750 > "$OUT/solve.log" 2> "$OUT/solve.err" ) &
pid=$!; start=$(date +%s); sleep 1; pg=$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
while kill -0 $pid 2>/dev/null; do sleep 5; if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill -TERM -- "-$pg" 2>/dev/null; sleep 10; kill -KILL -- "-$pg" 2>/dev/null; echo "KILLED_1800S" >> "$ST"; break; fi; done
wait $pid 2>/dev/null
grep -viE "$SCRUB" "$OUT/solve/gurobi.linopy.log" > "$OUT/GUROBI_LOG_SCRUBBED.txt" 2>/dev/null
grep -viE "$SCRUB" "$OUT/solve.log" > "$OUT/solve_log_scrubbed.txt" 2>/dev/null
"$PY" - "$OUT" "$REF" "$(( $(date +%s) - start ))" <<'P' | tee -a "$ST"
import json, re, sys
from pathlib import Path
out, ref_p, wall = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3])
ref = json.loads(ref_p.read_text()); rec = json.loads((out / "solve" / "SOLVE_RECEIPT.json").read_text()) if (out / "solve" / "SOLVE_RECEIPT.json").exists() else {}
it = sec = wu = None
for line in (out / "GUROBI_LOG_SCRUBBED.txt").read_text(errors="ignore").splitlines():
    m = re.match(r"Barrier solved model in (\d+) iterations and ([\d.]+) seconds(?: \(([\d.]+) work units\))?", line) or re.match(r"Barrier performed (\d+) iterations in ([\d.]+) seconds(?: \(([\d.]+) work units\))?", line)
    if m:
        it, sec, wu = int(m.group(1)), float(m.group(2)), (float(m.group(3)) if m.group(3) else None)
res = dict(termination=rec.get("termination_condition", "none"), objective=rec.get("objective"), barrier_iterations=it, barrier_seconds=sec, work_units=wu, wall_seconds=wall,
           seconds_per_work_unit=(sec / wu if (sec and wu) else None), seconds_per_iteration=(sec / it if (sec and it) else None), reference=ref)
if res["seconds_per_work_unit"] and ref.get("seconds_per_work_unit"):
    res["speed_ratio_instance_over_local_work_units"] = ref["seconds_per_work_unit"] / res["seconds_per_work_unit"]   # < 1 = the instance is slower
if res["seconds_per_iteration"] and ref.get("seconds_per_iteration"):
    res["speed_ratio_instance_over_local_iterations"] = ref["seconds_per_iteration"] / res["seconds_per_iteration"]
if res["objective"] and ref.get("objective"):
    res["objective_rel_diff_vs_local"] = res["objective"] / ref["objective"] - 1
r = res.get("speed_ratio_instance_over_local_work_units")
if r:
    # L23 (section 21): on a 0.23-0.30 x instance the integrated 365x24h run needed 1.7-3.1 h; scale the 4 h / 4.25 h defaults with the measured ratio relative to 0.25
    scale = max(1.0, 0.25 / r)
    res["suggested_gurobi_time_limit_s"] = int(round(14400 * scale / 300.0) * 300); res["suggested_wall_cap_s"] = res["suggested_gurobi_time_limit_s"] + 900
    res["suggestion_note"] = "defaults 14,400 / 15,300 s hold for an instance at least as fast as 0.25 x local (L23 instance 0.23-0.30); slower instances scale the caps by 0.25 / ratio"
(out / "SPEED_PROBE.json").write_text(json.dumps(res, indent=1))
print("SPEED_PROBE:", json.dumps({k: v for k, v in res.items() if k != "reference"}))
P
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$ST"
cat "$ST"
