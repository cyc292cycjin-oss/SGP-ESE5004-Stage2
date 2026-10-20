#!/bin/bash
# S4Q-1 (decision 123): script tests of the two S4Q changes of the S4O run pipeline (run_365x24h.sh) WITHOUT Gurobi and without the real licence:
#   N1  candidate profile formal_barrier_1e6 accepted, recorded in STATUS and passed to the solver; FIXED_RUNS=on with three optimal runs (gaps kept);
#   N2  formal_barrier_1e6_t16 + FIXED_RUNS=on: integrated non-optimal and C1 failed (REAL C1: no arrays -> not computable) -> NO stop, disconnected
#       and NZE still solved;
#   N3  FIXED_RUNS=on: disconnected non-optimal -> NO automatic disconnected_gap (exactly the three named solves), NZE still solved;
#   N4  FIXED_RUNS default off in the START line (dry run); invalid FIXED_RUNS refused;
#   N5  preflight profile section on the committed code snapshot accepts both candidates (key names, interior-point gate path) and keeps the default A.
# The S4O behaviour with FIXED_RUNS off (stop rule, automatic diagnostic, defaults) is covered by re-running the S4O harness (59 checks).
# Test doubles from the S4O harness: evidence/s4o_4/fake_s2_solve.py, fake_s4o_c1_precision.py.
#   bash test_s4q1_pipeline.sh <package dir with run_365x24h.sh + preflight.sh> <repo root (committed HEAD is archived for N5)> <out dir>
set -u
PKG=${1:?package dir}; ROOT=${2:?repo root}; OUT=${3:?out dir}
PY=${PY:-python3}
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"; PKG="$(cd "$PKG" && pwd)"; ROOT="$(cd "$ROOT" && pwd)"
FAKES="$ROOT/research/06_scope_redesign/p1_step4o_20261019/evidence/s4o_4"
RES="$OUT/TEST_RESULTS_s4q1.txt"; : > "$RES"
T=$(mktemp -d "${TMPDIR:-/tmp}/s4q1_test_XXXX"); echo "temp dir $T" >> "$RES"
pass=0; fail=0
check() { if eval "$2"; then echo "PASS: $1" >> "$RES"; pass=$((pass + 1)); else echo "FAIL: $1" >> "$RES"; fail=$((fail + 1)); fi; }
setup_pkg() {   # $1 dir $2 c1 kind: fake | real
  mkdir -p "$1/networks" "$1/repo/scripts_project" "$1/repo/configs/research"
  cp "$PKG/run_365x24h.sh" "$PKG/preflight.sh" "$1/"
  cp "$FAKES/fake_s2_solve.py" "$1/repo/scripts_project/s2_solve.py"
  if [ "${2:-fake}" = real ]; then cp "$ROOT/scripts_project/s4o_c1_precision.py" "$1/repo/scripts_project/"; else cp "$FAKES/fake_s4o_c1_precision.py" "$1/repo/scripts_project/s4o_c1_precision.py"; fi
  cp "$ROOT/configs/research/baseline.yaml" "$1/repo/configs/research/"
  for f in integrated disconnected integrated_nze disconnected_gap_diagnostic; do echo dummy > "$1/networks/${f}_365_24h_unsolved.nc"; done
  echo "0000000000000000000000000000000000000000" > "$1/COMMIT"
  echo "DUMMY LICENCE PATH FOR SCRIPT TESTS - NOT A LICENCE" > "$1/dummy.lic"
}
mkdir -p "$T/cg"; echo max > "$T/cg/memory.max"; echo 7516192768 > "$T/cg/memory.current"
# ---------------------------------------------------------------- N1
N1="$T/N1"; setup_pkg "$N1"
( cd "$N1" && FIXED_RUNS=on FAKE_SOLVE_S=2 WALL_CAP_S=60 MONITOR_S=1 RUN_GAP_S=4 CGROUP_ROOT="$T/cg" PY="$PY" GRB_LICENSE_FILE="$N1/dummy.lic" \
  bash run_365x24h.sh --solver-profile formal_barrier_1e6 --mode serial --runs integrated,disconnected,integrated_nze --auth "S4Q-1 script test N1" > "$OUT/N1_stdout.txt" 2>&1 )
S1=$(ls -d "$N1"/runs/*/ | head -1); cp "$S1/STATUS.txt" "$OUT/N1_STATUS.txt" 2>/dev/null
check "N1: candidate formal_barrier_1e6 accepted, in the START line with fixed_runs:on, passed to the solver" "grep -q 'solver_profile:formal_barrier_1e6 .*profile_source:--solver-profile.*fixed_runs:on' '$OUT/N1_STATUS.txt' && ( for t in integrated disconnected integrated_nze; do grep -q '\"solver_profile\": \"formal_barrier_1e6\"' \"$S1/\$t/SOLVE_RECEIPT.json\" || exit 1; done )"
check "N1: three optimal runs with C1 lines, gap >= RUN_GAP_S before the 2nd and 3rd solve, DONE" "[ \$(grep -c '^RUN_.*:optimal:' '$OUT/N1_STATUS.txt') -eq 3 ] && [ \$(grep -c '^PRECISION_' '$OUT/N1_STATUS.txt') -eq 3 ] && ( for t in disconnected integrated_nze; do s=\$(grep \"^GAP_\$t:\" '$OUT/N1_STATUS.txt' | cut -d: -f2 | tr -d s); [ -n \"\$s\" ] && [ \"\$s\" -ge 4 ] || exit 1; done ) && grep -q '^DONE:' '$OUT/N1_STATUS.txt'"
# ---------------------------------------------------------------- N2
N2="$T/N2"; setup_pkg "$N2" real
( cd "$N2" && FIXED_RUNS=on FAKE_SOLVE_S=2 FAKE_COND_integrated=suboptimal WALL_CAP_S=60 MONITOR_S=1 RUN_GAP_S=3 CGROUP_ROOT="$T/cg" PY="$PY" GRB_LICENSE_FILE="$N2/dummy.lic" \
  bash run_365x24h.sh --solver-profile formal_barrier_1e6_t16 --mode serial --runs integrated,disconnected,integrated_nze --auth "S4Q-1 script test N2" > "$OUT/N2_stdout.txt" 2>&1 )
S2=$(ls -d "$N2"/runs/*/ | head -1); cp "$S2/STATUS.txt" "$OUT/N2_STATUS.txt" 2>/dev/null
check "N2: formal_barrier_1e6_t16 accepted and passed to the solver" "grep -q 'solver_profile:formal_barrier_1e6_t16 ' '$OUT/N2_STATUS.txt' && grep -q '\"solver_profile\": \"formal_barrier_1e6_t16\"' '$S2/integrated/SOLVE_RECEIPT.json'"
check "N2: integrated non-optimal + real C1 not computable -> no STOP (NO_STOP line), disconnected and NZE solved" "grep -q '^PRECISION_integrated:not_computable:accepted=False:abc=000' '$OUT/N2_STATUS.txt' && grep -q '^NO_STOP_FIXED_RUNS_INTEGRATED_NONOPTIMAL_C1_FAILED:suboptimal' '$OUT/N2_STATUS.txt' && ! grep -q '^STOP_' '$OUT/N2_STATUS.txt' && ! test -e '$S2/STOP' && grep -q '^RUN_disconnected:optimal' '$OUT/N2_STATUS.txt' && grep -q '^RUN_integrated_nze:optimal' '$OUT/N2_STATUS.txt' && grep -q '^DONE:' '$OUT/N2_STATUS.txt'"
# ---------------------------------------------------------------- N3
N3="$T/N3"; setup_pkg "$N3"
( cd "$N3" && FIXED_RUNS=on FAKE_SOLVE_S=2 FAKE_COND_disconnected=suboptimal WALL_CAP_S=60 MONITOR_S=1 RUN_GAP_S=3 CGROUP_ROOT="$T/cg" PY="$PY" GRB_LICENSE_FILE="$N3/dummy.lic" \
  bash run_365x24h.sh --solver-profile formal_barrier_1e6 --mode serial --runs integrated,disconnected,integrated_nze --auth "S4Q-1 script test N3" > "$OUT/N3_stdout.txt" 2>&1 )
S3=$(ls -d "$N3"/runs/*/ | head -1); cp "$S3/STATUS.txt" "$OUT/N3_STATUS.txt" 2>/dev/null
check "N3: disconnected non-optimal -> no disconnected_gap solve (exactly 3 solves), said so, NZE solved" "grep -q '^NO_GAP_DIAGNOSTIC_FIXED_RUNS_DISCONNECTED_NON_OPTIMAL:suboptimal' '$OUT/N3_STATUS.txt' && ! grep -q '^SOLVE_disconnected_gap' '$OUT/N3_STATUS.txt' && ! grep -q '^DISCONNECTED_MAIN_NON_OPTIMAL' '$OUT/N3_STATUS.txt' && [ \$(grep -c '^SOLVE_' '$OUT/N3_STATUS.txt') -eq 3 ] && grep -q '^RUN_integrated_nze:optimal' '$OUT/N3_STATUS.txt'"
# ---------------------------------------------------------------- N4
N4="$T/N4"; setup_pkg "$N4"
( cd "$N4" && PY="$PY" GRB_LICENSE_FILE="$N4/dummy.lic" bash run_365x24h.sh --mode serial --dry-run > "$OUT/N4_dryrun.txt" 2>&1 ); rc4=$?
( cd "$N4" && FIXED_RUNS=yes PY="$PY" GRB_LICENSE_FILE="$N4/dummy.lic" bash run_365x24h.sh --mode serial --dry-run > "$OUT/N4_bad.txt" 2>&1 ); rc4b=$?
check "N4: default FIXED_RUNS off (START line), default profile formal_barrier; invalid value refused" "[ $rc4 -eq 0 ] && grep -q 'solver_profile:formal_barrier .*fixed_runs:off' '$OUT/N4_dryrun.txt' && [ $rc4b -eq 2 ] && grep -q 'FIXED_RUNS must be on or off' '$OUT/N4_bad.txt'"
# ---------------------------------------------------------------- N5
N5="$T/N5"; mkdir -p "$N5/repo"; cp "$PKG/preflight.sh" "$N5/"; ( cd "$ROOT" && git archive HEAD scripts_project configs | tar x -C "$N5/repo" )
for p in formal_barrier_1e6 formal_barrier_1e6_t16; do
  ( cd "$N5" && PREFLIGHT_ONLY=profile PY="$PY" bash preflight.sh serial $p > "$OUT/N5_preflight_$p.txt" 2>&1 ); echo "exit $?" >> "$OUT/N5_preflight_$p.txt"
done
( cd "$N5" && PREFLIGHT_ONLY=profile PY="$PY" bash preflight.sh serial > "$OUT/N5_preflight_default.txt" 2>&1 ); echo "exit $?" >> "$OUT/N5_preflight_default.txt"
check "N5: preflight on the committed snapshot accepts both candidates with the interior-point gate path; default stays formal_barrier" "grep -q \"^formal_barrier_1e6 (given).*'BarConvTol': 1e-06.*'Threads': 8.*interior-point gate path: True\" '$OUT/N5_preflight_formal_barrier_1e6.txt' && grep -q \"^formal_barrier_1e6_t16 (given).*'BarConvTol': 1e-06.*'Threads': 16.*interior-point gate path: True\" '$OUT/N5_preflight_formal_barrier_1e6_t16.txt' && grep -q '^formal_barrier (default)' '$OUT/N5_preflight_default.txt' && grep -q 'PREFLIGHT OK' '$OUT/N5_preflight_formal_barrier_1e6.txt' && grep -q 'PREFLIGHT OK' '$OUT/N5_preflight_formal_barrier_1e6_t16.txt'"
check "N6: script passes bash -n and holds no licence keyword" "bash -n '$PKG/run_365x24h.sh' && ! grep -iE 'wls(access|secret)|license[i]d' '$PKG/run_365x24h.sh' >/dev/null"
echo "SUMMARY: pass=$pass fail=$fail (temp $T)" >> "$RES"
cat "$RES"
rm -rf "$T"
[ $fail -eq 0 ]
