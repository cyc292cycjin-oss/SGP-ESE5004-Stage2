#!/bin/bash
# S4O-4: local tests of the S4O deployment scripts (run_365x24h.sh, preflight.sh) WITHOUT Gurobi, without the cloud and without the real licence
# file. The S4M-3 harness (cases A-E: wall-clock kill of the process group, receipts, refusals, dry run, cgroup quotas, syntax / licence keywords)
# adapted to the S4O defaults, plus the S4O pipeline (cases B, F, G, H): default profile pypsa_eur_default, C1 step after every solve with its
# STATUS lines and exports, the >= 5 min gap between serial solves (shortened through RUN_GAP_S), the batch reference + re-grading, the stop rule
# "integrated non-optimal and C1 failed", and the preflight profile / C1 sections on the real code. Test doubles: fake_s2_solve.py (solver),
# fake_s4o_c1_precision.py (C1 with a chosen grade); cases F and G use the REAL scripts_project/s4o_c1_precision.py.
#   bash test_s4o4_scripts.sh <package dir with run_365x24h.sh + preflight.sh> <repo root> <out dir>
set -u
PKG=${1:?package dir}; ROOT=${2:?repo root}; OUT=${3:?out dir}; HERE="$(cd "$(dirname "$0")" && pwd)"
PY=${PY:-python3}
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"; PKG="$(cd "$PKG" && pwd)"; ROOT="$(cd "$ROOT" && pwd)"
RES="$OUT/TEST_RESULTS.txt"; : > "$RES"
T=$(mktemp -d "${TMPDIR:-/tmp}/s4o4_test_XXXX"); echo "temp dir $T (set TMPDIR to a disk with >= 35 GiB free: the preflight disk check runs there)" >> "$RES"
pass=0; fail=0
check() { if eval "$2"; then echo "PASS: $1" >> "$RES"; pass=$((pass + 1)); else echo "FAIL: $1" >> "$RES"; fail=$((fail + 1)); fi; }
setup_pkg() {   # $1 dir $2 c1 kind: fake | real
  mkdir -p "$1/networks" "$1/repo/scripts_project" "$1/repo/configs/research"
  cp "$PKG/run_365x24h.sh" "$PKG/preflight.sh" "$1/"
  cp "$HERE/fake_s2_solve.py" "$1/repo/scripts_project/s2_solve.py"
  if [ "${2:-fake}" = real ]; then cp "$ROOT/scripts_project/s4o_c1_precision.py" "$1/repo/scripts_project/"; else cp "$HERE/fake_s4o_c1_precision.py" "$1/repo/scripts_project/s4o_c1_precision.py"; fi
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
( cd "$A" && FAKE_SOLVE_S=120 FAKE_MARKER=s4o4-killtest WALL_CAP_S=20 GRACE_S=5 MONITOR_S=2 GUROBI_TIME_LIMIT_S=15 CGROUP_ROOT="$T/cgA" PY="$PY" GRB_LICENSE_FILE="$A/dummy.lic" \
  bash run_365x24h.sh --mode serial --runs integrated --auth "S4O-4 script test A" > "$OUT/A_stdout.txt" 2>&1 )
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
check "A: whole script finished within 90 s (cap 20 s + grace + C1 + export)" "[ $tA -le 90 ]"
check "A: monitor has the cgroup columns and a limit of 90.00 GiB" "head -1 '$OUT/A_MONITOR_integrated.csv' | grep -q cgroup_mem_limit_gib && grep -q ',90.00,' '$OUT/A_MONITOR_integrated.csv'"
check "A: cgroup memory limit line in STATUS" "grep -q '^CGROUP_MEMORY_LIMIT_GIB:90.00' '$OUT/A_STATUS.txt'"
check "A: default profile pypsa_eur_default (no --solver-profile given)" "grep -q 'solver_profile:pypsa_eur_default .*profile_source:default_(decision_120)' '$OUT/A_STATUS.txt'"
check "A: killed run still gets its C1 line (fake C1)" "grep -q '^PRECISION_integrated:' '$OUT/A_STATUS.txt'"
check "A: killed pre-solve integrated with C1 passed (fake 111) -> no STOP" "! grep -q '^STOP_' '$OUT/A_STATUS.txt'"
# ---------------------------------------------------------------- B: normal completion -> post-solve receipts, C1 lines, gap, batch reference + re-grade
B="$T/B"; setup_pkg "$B"
tB0=$(date +%s)
( cd "$B" && FAKE_SOLVE_S=3 WALL_CAP_S=60 MONITOR_S=1 RUN_GAP_S=8 CGROUP_ROOT="$T/cgA" PY="$PY" GRB_LICENSE_FILE="$B/dummy.lic" \
  bash run_365x24h.sh --solver-profile formal_barrier --mode serial --runs integrated,disconnected,integrated_nze --auth "S4O-4 script test B" > "$OUT/B_stdout.txt" 2>&1 )
STB=$(ls -d "$B"/runs/*/ | head -1); cp "$STB/STATUS.txt" "$OUT/B_STATUS.txt" 2>/dev/null
check "B: explicit profile formal_barrier accepted and passed to the solver" "grep -q 'solver_profile:formal_barrier .*profile_source:--solver-profile' '$OUT/B_STATUS.txt' && grep -q '\"solver_profile\": \"formal_barrier\"' '$STB/integrated/SOLVE_RECEIPT.json'"
check "B: receipts recognised as post-solve" "[ \$(grep -c '^RECEIPT_.*:post_solve' '$OUT/B_STATUS.txt') -eq 3 ]"
check "B: all three runs optimal from the receipt" "grep -q '^RUN_integrated:optimal:' '$OUT/B_STATUS.txt' && grep -q '^RUN_disconnected:optimal:' '$OUT/B_STATUS.txt' && grep -q '^RUN_integrated_nze:optimal:' '$OUT/B_STATUS.txt'"
check "B: no kill line" "! grep -q '^KILLED' '$OUT/B_STATUS.txt'"
check "B: C1 line per run, accepted, L23 reference for the first two" "grep -q '^PRECISION_integrated:layer1_plus_nodal_price_settlement:accepted=True:abc=111:ref=L23:exit=0' '$OUT/B_STATUS.txt' && grep -q '^PRECISION_disconnected:.*:ref=L23:exit=0' '$OUT/B_STATUS.txt'"
check "B: batch reference built after the disconnected run, before NZE" "awk '/^BATCH_REFERENCE:/{b=NR} /^SOLVE_integrated_nze:/{s=NR} END{exit !(b && s && b < s)}' '$OUT/B_STATUS.txt'"
check "B: integrated and disconnected re-graded with the batch reference" "grep -q '^REGRADE_integrated:.*:ref=batch:exit=0' '$OUT/B_STATUS.txt' && grep -q '^REGRADE_disconnected:.*:ref=batch:exit=0' '$OUT/B_STATUS.txt'"
check "B: NZE C1 uses the batch reference directly (no re-grade needed)" "grep -q '^PRECISION_integrated_nze:.*:ref=batch:exit=0' '$OUT/B_STATUS.txt' && ! grep -q '^REGRADE_integrated_nze' '$OUT/B_STATUS.txt'"
check "B: gap >= RUN_GAP_S before the 2nd and 3rd solve" "for t in disconnected integrated_nze; do s=\$(grep \"^GAP_\$t:\" '$OUT/B_STATUS.txt' | cut -d: -f2 | tr -d s); [ -n \"\$s\" ] && [ \"\$s\" -ge 8 ] || exit 1; done"
check "B: exported PRECISION.json / .md and EXPORTS.json listing them (re-graded copy in the export)" "for t in integrated disconnected integrated_nze; do for f in PRECISION.json PRECISION.md EXPORTS.json; do test -f \"$STB/export/\$t/\$f\" || exit 1; done; grep -q PRECISION.json \"$STB/export/\$t/EXPORTS.json\" || exit 1; done && grep -q regraded '$STB/export/integrated/PRECISION.json' && test -f '$STB/export/BATCH_REFERENCE.json'"
check "B: S4M supplement exports still copied" "for f in DUALS_BY_CONSTRAINT.nc DUALS_INDEX.csv COMPONENT_COST_BREAKDOWN.csv COMPONENT_COST_BREAKDOWN_SUMMARY.json costs_active_research.csv EXPORTS.json; do test -f \"$STB/export/integrated/\$f\" || exit 1; done"
check "B: --costs-table points at networks/<tag>_costs_active_research.csv" "grep -q 'networks/integrated_costs_active_research.csv' '$STB/integrated/COSTS_TABLE_ARG.txt'"
check "B: C1 runs without GRB_LICENSE_FILE in its environment and without the licence path in its arguments" "grep -q '\"licence_env\": false' '$STB/integrated/PRECISION.json' && ! grep -q dummy.lic '$STB/integrated/PRECISION.json'"
check "B: no solver process survived" "! pgrep -f 'repo/scripts_project/s2_solve.py --repo $B/repo' >/dev/null"
check "B: DONE and tarball" "grep -q '^DONE:' '$OUT/B_STATUS.txt' && ls '$STB'/results_*.tar.gz >/dev/null 2>&1"
# ---------------------------------------------------------------- C: refusals and dry run
C="$T/C"; setup_pkg "$C"
( cd "$C" && PY="$PY" GRB_LICENSE_FILE="$C/dummy.lic" bash run_365x24h.sh --mode lanes3 > "$OUT/C_lanes3.txt" 2>&1 ); rc1=$?
( cd "$C" && PY="$PY" GRB_LICENSE_FILE="$C/dummy.lic" bash run_365x24h.sh --solver-profile not_a_profile --mode serial > "$OUT/C_badprofile.txt" 2>&1 ); rc2=$?
( cd "$C" && PY="$PY" GRB_LICENSE_FILE="$C/dummy.lic" bash run_365x24h.sh --mode serial --dry-run > "$OUT/C_dryrun.txt" 2>&1 ); rc4=$?
check "C: lanes3 refused" "[ $rc1 -eq 2 ] && grep -q REFUSED '$OUT/C_lanes3.txt'"
check "C: unknown profile refused" "[ $rc2 -eq 2 ]"
check "C: dry run lists the three solve commands with the default profile pypsa_eur_default, --time-limit 14400, exits 0" "[ $rc4 -eq 0 ] && [ \$(grep -c 'DRY-RUN: .*s2_solve.py' '$OUT/C_dryrun.txt') -eq 3 ] && [ \$(grep -c 'DRY-RUN: .*s2_solve.py.*--solver-profile pypsa_eur_default' '$OUT/C_dryrun.txt') -eq 3 ] && grep -q -- '--time-limit 14400' '$OUT/C_dryrun.txt'"
check "C: dry run lists the C1 step for each run and the gap and batch reference" "[ \$(grep -c 'DRY-RUN: C1 .*l23_violation_analysis.py.*s4o_c1_precision.py run' '$OUT/C_dryrun.txt') -eq 3 ] && grep -q 'DRY-RUN: would wait until 330 s' '$OUT/C_dryrun.txt' && grep -q 'DRY-RUN: batch reference' '$OUT/C_dryrun.txt'"
check "C: production defaults in START line (wall cap 15300 s, TimeLimit 14400 s, gap 330 s, C1 on)" "grep -q 'wall_cap_s:15300 time_limit_s:14400 .*run_gap_s:330 c1_step:on' '$OUT/C_dryrun.txt'"
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
# ---------------------------------------------------------------- E: syntax and licence keywords
check "E: both scripts pass bash -n" "bash -n '$PKG/run_365x24h.sh' && bash -n '$PKG/preflight.sh'"
check "E: scripts hold no licence keyword outside the scrub pattern lines" "! grep -iE 'wls(access|secret)|license[i]d' '$PKG/run_365x24h.sh' '$PKG/preflight.sh' >/dev/null"
# ---------------------------------------------------------------- F: stop rule with the REAL C1 module (no solution arrays -> not computable -> C1 failed)
F="$T/F"; setup_pkg "$F" real
( cd "$F" && FAKE_SOLVE_S=2 FAKE_COND_integrated=suboptimal WALL_CAP_S=60 MONITOR_S=1 RUN_GAP_S=3 CGROUP_ROOT="$T/cgA" PY="$PY" GRB_LICENSE_FILE="$F/dummy.lic" \
  bash run_365x24h.sh --mode serial --auth "S4O-4 script test F" > "$OUT/F_stdout.txt" 2>&1 )
STF=$(ls -d "$F"/runs/*/ | head -1); cp "$STF/STATUS.txt" "$OUT/F_STATUS.txt" 2>/dev/null
check "F: real C1 reports the run without solution arrays as not computable" "grep -q '^PRECISION_integrated:not_computable:accepted=False:abc=000:ref=L23:exit=0' '$OUT/F_STATUS.txt' && grep -q '\"computable\": false' '$STF/export/integrated/PRECISION.json'"
check "F: integrated non-optimal + C1 failed -> STOP, no further solve" "grep -q '^STOP_INTEGRATED_NONOPTIMAL_C1_FAILED:suboptimal' '$OUT/F_STATUS.txt' && ! grep -q '^SOLVE_disconnected' '$OUT/F_STATUS.txt' && ! grep -q '^SOLVE_integrated_nze' '$OUT/F_STATUS.txt'"
check "F: still exported and packed (DONE)" "grep -q '^DONE:' '$OUT/F_STATUS.txt' && test -f '$STF/export/integrated/PRECISION.md'"
# ---------------------------------------------------------------- G: real C1 reference + re-grade from the two ledgers; non-optimal disconnected continues
G="$T/G"; setup_pkg "$G" real
( cd "$G" && FAKE_SOLVE_S=2 FAKE_COND_disconnected=suboptimal WALL_CAP_S=60 MONITOR_S=1 RUN_GAP_S=3 CGROUP_ROOT="$T/cgA" PY="$PY" GRB_LICENSE_FILE="$G/dummy.lic" \
  bash run_365x24h.sh --mode serial --auth "S4O-4 script test G" > "$OUT/G_stdout.txt" 2>&1 )
STG=$(ls -d "$G"/runs/*/ | head -1); cp "$STG/STATUS.txt" "$OUT/G_STATUS.txt" 2>/dev/null
check "G: batch reference from the two fake ledgers = +1 bn per country, ASEAN = +2 bn (bunker + pool)" "\"$PY\" -c \"import json,sys; r=json.load(open('$STG/BATCH_REFERENCE.json'))['differences_bn']; sys.exit(0 if abs(r['PH']-1)<1e-12 and abs(r['ASEAN']-2)<1e-12 else 1)\""
check "G: integrated optimal + disconnected non-optimal: no STOP, the gap diagnostic runs, NZE runs" "! grep -q '^STOP_' '$OUT/G_STATUS.txt' && grep -q '^DISCONNECTED_MAIN_NON_OPTIMAL:suboptimal' '$OUT/G_STATUS.txt' && grep -q '^RUN_disconnected_gap:optimal' '$OUT/G_STATUS.txt' && grep -q '^RUN_integrated_nze:optimal' '$OUT/G_STATUS.txt'"
check "G: real re-grade sets the batch reference on the earlier runs" "grep -q '^REGRADE_integrated:not_computable:accepted=False:abc=000:ref=batch:exit=0' '$OUT/G_STATUS.txt' && grep -q '^REGRADE_disconnected:.*ref=batch:exit=0' '$OUT/G_STATUS.txt'"
check "G: real C1 registers its outputs in EXPORTS.json" "\"$PY\" -c \"import json,sys; e=json.load(open('$STG/export/integrated/EXPORTS.json')); sys.exit(0 if {'PRECISION.json','PRECISION.md','DUALS_INDEX.csv'} <= set(e) else 1)\""
# ---------------------------------------------------------------- H: preflight profile + C1 sections on the REAL code snapshot (no licence, no Gurobi)
H="$T/H"; mkdir -p "$H/repo"; cp "$PKG/preflight.sh" "$H/"; ( cd "$ROOT" && git archive HEAD scripts_project configs | tar x -C "$H/repo" )
( cd "$H" && PREFLIGHT_ONLY=profile,c1 PY="$PY" bash preflight.sh serial > "$OUT/H_preflight_default.txt" 2>&1 ); echo "exit $?" >> "$OUT/H_preflight_default.txt"
( cd "$H" && PREFLIGHT_ONLY=profile PY="$PY" bash preflight.sh serial formal_barrier > "$OUT/H_preflight_A.txt" 2>&1 ); echo "exit $?" >> "$OUT/H_preflight_A.txt"
( cd "$H" && PREFLIGHT_ONLY=profile PY="$PY" bash preflight.sh serial nope > "$OUT/H_preflight_bad.txt" 2>&1 ); echo "exit $?" >> "$OUT/H_preflight_bad.txt"
check "H: default profile pypsa_eur_default found, key names accepted, interior-point gate path, C1 scripts present and importable" "grep -q '^pypsa_eur_default (default).*interior-point gate path: True' '$OUT/H_preflight_default.txt' && grep -q 's4o_c1_precision imports' '$OUT/H_preflight_default.txt' && grep -q 'PREFLIGHT OK' '$OUT/H_preflight_default.txt'"
check "H: explicit profile A accepted" "grep -q '^formal_barrier (given)' '$OUT/H_preflight_A.txt' && grep -q 'PREFLIGHT OK' '$OUT/H_preflight_A.txt'"
check "H: unknown profile fails the preflight" "grep -q 'UNKNOWN PROFILE nope' '$OUT/H_preflight_bad.txt' && grep -q 'PREFLIGHT FAILED' '$OUT/H_preflight_bad.txt'"
echo "SUMMARY: pass=$pass fail=$fail (temp $T)" >> "$RES"
cat "$RES"
rm -rf "$T"
[ $fail -eq 0 ]
