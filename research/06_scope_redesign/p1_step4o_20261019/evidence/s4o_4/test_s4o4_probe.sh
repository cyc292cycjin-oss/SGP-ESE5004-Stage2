#!/bin/bash
# S4O supplement 01 copy of the S4M-3 probe harness: expected suggestions with the decision-121 base 21,600 s (A: 21,600 / 22,500; B: 27,000 / 27,900).
# S4M-3 local test of speed_probe.sh (no Gurobi, no cloud): a temp package folder with the probe script, a dummy probe network file, a PROBE_REFERENCE.json
# of the local S4M-2 integrated smoke (or synthetic values) and the test double fake_s2_solve_probe.py that reports a slower 'instance' (x 2 seconds per work
# unit) -> the probe must compute the ratio 0.5 and suggest scaled caps; a second case with the same speed must keep the defaults 14,400 / 15,300.
#   bash test_s4m3_probe.sh <package dir with speed_probe.sh> <out dir>
set -u
PKG="$(cd "${1:?package dir}" && pwd)"; OUT="${2:?out dir}"; mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"; HERE="$(cd "$(dirname "$0")" && pwd)"
PY=${PY:-python3}; RES="$OUT/TEST_RESULTS_probe.txt"; : > "$RES"; pass=0; fail=0
check() { if eval "$2"; then echo "PASS: $1" >> "$RES"; pass=$((pass + 1)); else echo "FAIL: $1" >> "$RES"; fail=$((fail + 1)); fi; }
T=$(mktemp -d "${TMPDIR:-/tmp}/s4m3_probe_XXXX")
setup() { local d=$1; mkdir -p "$d/networks" "$d/repo/scripts_project"; cp "$PKG/speed_probe.sh" "$d/"; cp "$HERE/fake_s2_solve_probe.py" "$d/repo/scripts_project/s2_solve.py"
  echo dummy > "$d/networks/integrated_56_3h_probe_unsolved.nc"; echo "0000000000000000000000000000000000000000" > "$d/COMMIT"; echo "DUMMY LICENCE PATH FOR SCRIPT TESTS - NOT A LICENCE" > "$d/dummy.lic"
  "$PY" - "$d/PROBE_REFERENCE.json" <<'P'
import json, sys
json.dump(dict(run="synthetic local reference", objective=648262301211.7622, barrier_iterations=136, barrier_seconds=200.88, work_units=356.76, seconds_per_work_unit=200.88 / 356.76, seconds_per_iteration=200.88 / 136), open(sys.argv[1], "w"))
P
}
A="$T/A"; setup "$A"
( cd "$A" && FAKE_BARRIER="136 401.76 356.76" PY="$PY" GRB_LICENSE_FILE="$A/dummy.lic" bash speed_probe.sh --auth "S4M-3 probe test A" > "$OUT/probe_A_stdout.txt" 2>&1 ); rcA=$?
PA=$(ls -d "$A"/probe/*/ | head -1); cp "$PA/SPEED_PROBE.json" "$OUT/probe_A_SPEED_PROBE.json" 2>/dev/null; cp "$PA/STATUS.txt" "$OUT/probe_A_STATUS.txt" 2>/dev/null
check "A: probe script exits 0" "[ $rcA -eq 0 ]"
check "A: slower instance (2 x seconds per work unit) -> ratio 0.5" "\"$PY\" -c \"import json,sys; r=json.load(open('$OUT/probe_A_SPEED_PROBE.json')); sys.exit(0 if abs(r['speed_ratio_instance_over_local_work_units']-0.5)<1e-9 else 1)\""
check "A: ratio 0.5 is faster than 0.25: scale = max(1, 0.5) = 1 -> the decision-121 defaults 21,600 / 22,500" "\"$PY\" -c \"import json,sys; r=json.load(open('$OUT/probe_A_SPEED_PROBE.json')); sys.exit(0 if (r['suggested_gurobi_time_limit_s']==21600 and r['suggested_wall_cap_s']==22500) else 1)\""
check "A: objective difference vs local reported as 0" "\"$PY\" -c \"import json,sys; r=json.load(open('$OUT/probe_A_SPEED_PROBE.json')); sys.exit(0 if abs(r['objective_rel_diff_vs_local'])<1e-12 else 1)\""
check "A: STATUS has START with the cpu model and DONE" "grep -q '^START:.*cpu:' '$OUT/probe_A_STATUS.txt' && grep -q '^DONE:' '$OUT/probe_A_STATUS.txt'"
B="$T/B"; setup "$B"
( cd "$B" && FAKE_BARRIER="136 1004.4 356.76" PY="$PY" GRB_LICENSE_FILE="$B/dummy.lic" bash speed_probe.sh > "$OUT/probe_B_stdout.txt" 2>&1 ); rcB=$?
PB=$(ls -d "$B"/probe/*/ | head -1); cp "$PB/SPEED_PROBE.json" "$OUT/probe_B_SPEED_PROBE.json" 2>/dev/null
check "B: 5 x slower instance -> ratio 0.2, caps scaled by 0.25/0.2 = 1.25 -> 27,000 / 27,900 s" "\"$PY\" -c \"import json,sys; r=json.load(open('$OUT/probe_B_SPEED_PROBE.json')); sys.exit(0 if (abs(r['speed_ratio_instance_over_local_work_units']-0.2)<1e-9 and r['suggested_gurobi_time_limit_s']==27000 and r['suggested_wall_cap_s']==27900) else 1)\""
C="$T/C"; setup "$C"; rm "$C/PROBE_REFERENCE.json"
( cd "$C" && PY="$PY" GRB_LICENSE_FILE="$C/dummy.lic" bash speed_probe.sh > "$OUT/probe_C_stdout.txt" 2>&1 ); rcC=$?
check "C: missing PROBE_REFERENCE.json refused (exit 2)" "[ $rcC -eq 2 ]"
check "D: bash -n speed_probe.sh" "bash -n '$PKG/speed_probe.sh'"
check "E: no licence keyword in speed_probe.sh" "! grep -iE 'wls(access|secret)|license[i]d' '$PKG/speed_probe.sh' >/dev/null"
echo "SUMMARY: pass=$pass fail=$fail" >> "$RES"; cat "$RES"; rm -rf "$T"; [ $fail -eq 0 ]
