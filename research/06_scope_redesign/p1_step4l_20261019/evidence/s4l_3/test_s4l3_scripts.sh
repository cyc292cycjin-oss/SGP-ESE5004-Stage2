#!/bin/bash
# S4L-3 point 4: local tests of the corrected deployment scripts (run_365x24h.sh, preflight.sh) WITHOUT Gurobi, without the cloud and without the
# real licence file: a temporary package folder with a test double of s2_solve.py (fake_s2_solve.py), dummy networks, a dummy licence path and
# fake cgroup trees. Everything runs with short caps (seconds) through the test-only environment overrides.
#   bash test_s4l3_scripts.sh <package dir with run_365x24h.sh + preflight.sh> <repo root> <out dir>
# Writes <out>/TEST_RESULTS.txt (one PASS/FAIL line per check) and keeps the STATUS / MONITOR files of every run.
set -u
PKG=${1:?package dir}; ROOT=${2:?repo root}; OUT=${3:?out dir}; HERE="$(cd "$(dirname "$0")" && pwd)"
PY=${PY:-python3}
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"; PKG="$(cd "$PKG" && pwd)"; ROOT="$(cd "$ROOT" && pwd)"   # absolute: the runs below cd into temp folders
RES="$OUT/TEST_RESULTS.txt"; : > "$RES"
T=$(mktemp -d "${TMPDIR:-/tmp}/s4l3_test_XXXX"); echo "temp dir $T (set TMPDIR to a disk with >= 35 GiB free: the preflight disk check runs there)" >> "$RES"
pass=0; fail=0
check() { if eval "$2"; then echo "PASS: $1" >> "$RES"; pass=$((pass + 1)); else echo "FAIL: $1" >> "$RES"; fail=$((fail + 1)); fi; }
setup_pkg() {   # $1 dir
  mkdir -p "$1/networks" "$1/repo/scripts_project" "$1/repo/configs/research"
  cp "$PKG/run_365x24h.sh" "$PKG/preflight.sh" "$1/"
  cp "$HERE/fake_s2_solve.py" "$1/repo/scripts_project/s2_solve.py"
  cp "$ROOT/configs/research/baseline.yaml" "$1/repo/configs/research/"
  for f in integrated disconnected integrated_nze disconnected_gap_diagnostic; do echo dummy > "$1/networks/${f}_365_24h_unsolved.nc"; done
  echo "0000000000000000000000000000000000000000" > "$1/COMMIT"
  echo "DUMMY LICENCE PATH FOR SCRIPT TESTS - NOT A LICENCE" > "$1/dummy.lic"
}
mk_cgroup() {   # $1 dir $2 kind: v2|v1|v2max|v1max
  mkdir -p "$1/cpu" "$1/memory"
  case "$2" in
    v2) echo "1200000 100000" > "$1/cpu.max"; echo 96636764160 > "$1/memory.max"; echo 7516192768 > "$1/memory.current";;
    v2max) echo "max 100000" > "$1/cpu.max"; echo max > "$1/memory.max"; echo 7516192768 > "$1/memory.current";;
    v1) echo 800000 > "$1/cpu/cpu.cfs_quota_us"; echo 100000 > "$1/cpu/cpu.cfs_period_us"; echo 42949672960 > "$1/memory/memory.limit_in_bytes"; echo 5368709120 > "$1/memory/memory.usage_in_bytes";;
    v1max) echo -1 > "$1/cpu/cpu.cfs_quota_us"; echo 100000 > "$1/cpu/cpu.cfs_period_us"; echo 9223372036854771712 > "$1/memory/memory.limit_in_bytes"; echo 5368709120 > "$1/memory/memory.usage_in_bytes";;
  esac
}
# ---------------------------------------------------------------- A: wall-clock kill ends the whole process group, receipt stays pre-solve
A="$T/A"; setup_pkg "$A"; mk_cgroup "$T/cgA" v2
t0=$(date +%s)
( cd "$A" && FAKE_SOLVE_S=120 FAKE_MARKER=s4l3-killtest WALL_CAP_S=20 GRACE_S=5 MONITOR_S=2 GUROBI_TIME_LIMIT_S=15 CGROUP_ROOT="$T/cgA" PY="$PY" GRB_LICENSE_FILE="$A/dummy.lic" \
  bash run_365x24h.sh --solver-profile formal_barrier --mode serial --runs integrated --auth "S4L-3 script test A" > "$OUT/A_stdout.txt" 2>&1 )
tA=$(( $(date +%s) - t0 ))
STA=$(ls -d "$A"/runs/*/ | head -1); cp "$STA/STATUS.txt" "$OUT/A_STATUS.txt" 2>/dev/null; cp "$STA/MONITOR_integrated.csv" "$OUT/A_MONITOR_integrated.csv" 2>/dev/null
sleep 2
check "A: kill line written at the cap" "grep -q '^KILLED_20S_integrated:' '$OUT/A_STATUS.txt'"
check "A: receipt recognised as pre-solve" "grep -q '^RECEIPT_integrated:pre_solve' '$OUT/A_STATUS.txt'"
check "A: run marked killed_pre_solve" "grep -q '^RUN_integrated:killed_pre_solve:' '$OUT/A_STATUS.txt'"
check "A: no solver process of the group survived (python test double)" "! pgrep -f 'repo/scripts_project/s2_solve.py --repo $A/repo' >/dev/null"
check "A: no grandchild (sleep 600) survived" "! pgrep -f 'sleep 600' -u \$(id -u) >/dev/null || ! ps -o ppid= -p \$(pgrep -f 'sleep 600' | head -1) 2>/dev/null | grep -q ."
check "A: export folder holds the pre-solve receipt" "test -f '$STA/export/integrated/SOLVE_RECEIPT.json' && ! grep -q termination_condition '$STA/export/integrated/SOLVE_RECEIPT.json'"
check "A: DONE after the kill and the results tarball exists" "grep -q '^DONE:' '$OUT/A_STATUS.txt' && ls '$STA'/results_*.tar.gz >/dev/null 2>&1"
check "A: whole script finished within 90 s (cap 20 s + grace + export)" "[ $tA -le 90 ]"
check "A: monitor has the cgroup columns and a limit of 90.00 GiB" "head -1 '$OUT/A_MONITOR_integrated.csv' | grep -q cgroup_mem_limit_gib && grep -q ',90.00,' '$OUT/A_MONITOR_integrated.csv'"
check "A: cgroup memory limit line in STATUS" "grep -q '^CGROUP_MEMORY_LIMIT_GIB:90.00' '$OUT/A_STATUS.txt'"
# ---------------------------------------------------------------- B: normal completion -> post-solve receipt, termination from the receipt
B="$T/B"; setup_pkg "$B"
( cd "$B" && FAKE_SOLVE_S=3 WALL_CAP_S=60 MONITOR_S=1 CGROUP_ROOT="$T/cgA" PY="$PY" GRB_LICENSE_FILE="$B/dummy.lic" \
  bash run_365x24h.sh --solver-profile formal_barrier_crossover --mode serial --runs integrated,disconnected --auth "S4L-3 script test B" > "$OUT/B_stdout.txt" 2>&1 )
STB=$(ls -d "$B"/runs/*/ | head -1); cp "$STB/STATUS.txt" "$OUT/B_STATUS.txt" 2>/dev/null
check "B: new profile formal_barrier_crossover accepted" "grep -q 'solver_profile:formal_barrier_crossover' '$OUT/B_STATUS.txt'"
check "B: receipts recognised as post-solve" "[ \$(grep -c '^RECEIPT_.*:post_solve' '$OUT/B_STATUS.txt') -eq 2 ]"
check "B: both runs optimal from the receipt" "grep -q '^RUN_integrated:optimal:' '$OUT/B_STATUS.txt' && grep -q '^RUN_disconnected:optimal:' '$OUT/B_STATUS.txt'"
check "B: no kill line" "! grep -q '^KILLED' '$OUT/B_STATUS.txt'"
check "B: exported post-solve receipt" "grep -q termination_condition '$STB/export/integrated/SOLVE_RECEIPT.json'"
check "B: no solver process survived" "! pgrep -f 'repo/scripts_project/s2_solve.py --repo $B/repo' >/dev/null"
# ---------------------------------------------------------------- C: refusals and dry run
C="$T/C"; setup_pkg "$C"
( cd "$C" && PY="$PY" GRB_LICENSE_FILE="$C/dummy.lic" bash run_365x24h.sh --solver-profile formal_barrier --mode lanes3 > "$OUT/C_lanes3.txt" 2>&1 ); rc1=$?
( cd "$C" && PY="$PY" GRB_LICENSE_FILE="$C/dummy.lic" bash run_365x24h.sh --solver-profile not_a_profile --mode serial > "$OUT/C_badprofile.txt" 2>&1 ); rc2=$?
( cd "$C" && PY="$PY" GRB_LICENSE_FILE="$C/dummy.lic" bash run_365x24h.sh --mode serial > "$OUT/C_noprofile.txt" 2>&1 ); rc3=$?
( cd "$C" && PY="$PY" GRB_LICENSE_FILE="$C/dummy.lic" bash run_365x24h.sh --solver-profile formal_barrier --mode serial --dry-run > "$OUT/C_dryrun.txt" 2>&1 ); rc4=$?
check "C: lanes3 refused" "[ $rc1 -eq 2 ] && grep -q REFUSED '$OUT/C_lanes3.txt'"
check "C: unknown profile refused" "[ $rc2 -eq 2 ]"
check "C: missing profile refused" "[ $rc3 -eq 2 ]"
check "C: dry run lists the three solve commands with --time-limit 10500 and exits 0" "[ $rc4 -eq 0 ] && [ \$(grep -c 'DRY-RUN: .*s2_solve.py' '$OUT/C_dryrun.txt') -eq 3 ] && grep -q -- '--time-limit 10500' '$OUT/C_dryrun.txt'"
check "C: production defaults in START line (wall cap 10800 s)" "grep -q 'wall_cap_s:10800 time_limit_s:10500' '$OUT/C_dryrun.txt'"
# ---------------------------------------------------------------- D: preflight resources from fake cgroup trees (sections resources + tools only)
D="$T/D"; setup_pkg "$D"
for kind in v2 v1 v2max v1max; do
  mk_cgroup "$T/cg_$kind" "$kind"
  ( cd "$D" && CGROUP_ROOT="$T/cg_$kind" PREFLIGHT_ONLY=resources,tools PY="$PY" bash preflight.sh serial > "$OUT/D_preflight_$kind.txt" 2>&1 ); echo "exit $?" >> "$OUT/D_preflight_$kind.txt"
done
check "D: cgroup v2 quota read (12 cores, 90 GiB) and PREFLIGHT OK" "grep -q 'container CPU cores 12 \[cgroup v2' '$OUT/D_preflight_v2.txt' && grep -q 'container memory 90 GiB \[cgroup v2' '$OUT/D_preflight_v2.txt' && grep -q 'PREFLIGHT OK' '$OUT/D_preflight_v2.txt'"
check "D: cgroup v1 quota read (8 cores, 40 GiB) and PREFLIGHT OK with the recommended-memory warning" "grep -q 'container CPU cores 8 \[cgroup v1' '$OUT/D_preflight_v1.txt' && grep -q 'container memory 40 GiB \[cgroup v1' '$OUT/D_preflight_v1.txt' && grep -q 'PREFLIGHT OK' '$OUT/D_preflight_v1.txt' && grep -q 'WARNING: memory below the recommended' '$OUT/D_preflight_v1.txt'"
check "D: cgroup v2 unlimited falls back to the host values and says so" "grep -q 'no cgroup CPU quota' '$OUT/D_preflight_v2max.txt' && grep -q 'no cgroup memory limit' '$OUT/D_preflight_v2max.txt'"
check "D: cgroup v1 unlimited (quota -1, limit 2^63) falls back to the host values" "grep -q 'no cgroup CPU quota' '$OUT/D_preflight_v1max.txt' && grep -q 'no cgroup memory limit' '$OUT/D_preflight_v1max.txt'"
check "D: tools section finds GNU time and setsid" "grep -q '/usr/bin/time (GNU time, -v) present' '$OUT/D_preflight_v2.txt' && grep -q 'setsid (util-linux) present' '$OUT/D_preflight_v2.txt'"
# ---------------------------------------------------------------- E: preflight full-file syntax and the licence section is untouched by the test (not run)
check "E: both scripts pass bash -n" "bash -n '$PKG/run_365x24h.sh' && bash -n '$PKG/preflight.sh'"
check "E: scripts hold no licence keyword outside the scrub pattern lines" "! grep -iE 'wlsaccess|wlssecret|licenseid' '$PKG/run_365x24h.sh' '$PKG/preflight.sh' >/dev/null"
echo "SUMMARY: pass=$pass fail=$fail (temp $T)" >> "$RES"
cat "$RES"
rm -rf "$T"
[ $fail -eq 0 ]
