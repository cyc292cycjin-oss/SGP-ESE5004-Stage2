#!/bin/bash
# V3.1 OPTIONAL (V3_FIX_INSTRUCTION.md 6.5; NOT run in the V3.1 step): full-year build + presolve-only probe of F1 and F2 on a machine with >= 256 GB of memory
# (e.g. an AutoDL instance), to see the v3.1 formulation pass Gurobi's presolve on the full 2920x3h model before or beside the HPC batch. Each network: process 1 =
# the runner's own build (scripts_project/s2_solve.py --split-stage build, no truncation, label SMOKE_TEST_ONLY, profile formal_barrier_1e6_t16, --scaling on; no licence),
# process 2 = the runner's scripts_project/b4_split_solve.py --probe-ordering-only (BarIterLimit 0, every other parameter from the profile) with the run protection
# MemLimit (hard, GB) = 80 % of the machine's memory. Verdict from the Gurobi log (as V3 DIAG): "infeasible or unbounded" -> INF_OR_UNBD (FAIL); a "Presolved:" line
# without it -> PRESOLVE_PASSED (the ordering after it may stop at MemLimit or end with ITERATION_LIMIT: both are passes). 2 Gurobi sessions, serial, >= 330 s apart.
#
# Estimates (INFERENCE; RUN_PLAN_HPC_V3.md sections 2.1, 9 and 15, V3_DIAG_REPORT.md section 10): process 1 about 40-50 min single-threaded, peak about 96-110 GiB,
# problem file about 5.5 GB plus LP arrays about 8 GB per network; process 2: LP read about 3 min, presolve 4-10 min, ordering 15-40 min, Gurobi memory 60-80 GB.
# Per network about 1.2-1.8 h, both about 2.5-3.5 h. Machine: >= 256 GB memory (refused below 250 GiB), >= 32 cores useful (Threads 16 of the profile), >= 60 GB
# free disk in the package folder.
# Upload (one stream, as for the HPC): the v3.1 package folder hpc_package_v3_1 (374.5 MB; only code_*.tar.gz, COMMIT, SHA256SUMS, BATCH_DEF.json, preflight.sh, env/
# and networks/integrated_2920_3h_unsolved.nc, networks/no_new_xb_2920_3h_unsolved.nc, networks/integrated_costs_active_research.csv are used), then
# "sha256sum -c SHA256SUMS" and the package preflight "PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools bash preflight.sh" (unpacks ./repo). The licence is
# placed by the user (GRB_LICENSE_FILE, default $HOME/gurobi.lic, mode 600; never in the package). No other Gurobi session with the same WLS licence may run at the
# same time (HPC, local machine).
# Expected output: runs/fullsize_presolve/FULLSIZE_PRESOLVE.txt with "F1:PRESOLVE_PASSED:Presolved: ... rows, ... columns, ... nonzeros" and the same for F2, the
# build seconds / peak memory / LP size per network and FULLSIZE_PRESOLVE_RESULT:PASS; Gurobi logs filtered for licence lines.
#
#   cd <uploaded package folder> && bash fullsize_presolve.sh --confirmed-by-user "authorisation text of the user (no account / host / licence content)"
set -u
[ "${1:-}" = "--confirmed-by-user" ] && [ -n "${2:-}" ] || { echo "REFUSED: needs --confirmed-by-user \"<text>\" - an optional step that uses 2 Gurobi sessions; run only on the user's authorisation"; exit 2; }
AUTH=$2
PKG=$(pwd); PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}; LIC=${GRB_LICENSE_FILE:-$HOME/gurobi.lic}
OUT=$PKG/runs/fullsize_presolve; ST=$OUT/FULLSIZE_PRESOLVE.txt; GAP=330
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic|accessid|secret'
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }; log() { echo "$*" | tee -a "$ST"; }
busy() { ps -eo args= | grep -E '[b]4_split_solve\.py|[s]2_solve\.py|[g]urobi_cl' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
token_ok() { timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null; }
verdict() { local L=$1
  if grep -qi "infeasible or unbounded" "$L" 2>/dev/null; then echo INF_OR_UNBD
  elif grep -qi "^Model is infeasible" "$L" 2>/dev/null; then echo INFEASIBLE
  elif grep -qi "^Model is unbounded\|^Unbounded model" "$L" 2>/dev/null; then echo UNBOUNDED
  elif grep -q "^Presolved:" "$L" 2>/dev/null; then echo PRESOLVE_PASSED
  else echo UNDECIDED; fi; }
[ -f COMMIT ] && [ -f BATCH_DEF.json ] && [ -d networks ] || { echo "REFUSED: run inside the uploaded v3.1 package folder"; exit 2; }
grep -q '"formal": "runs/batch5"' BATCH_DEF.json || { echo "REFUSED: not the v3.1 package (BATCH_DEF.json run_dirs)"; exit 2; }
[ "$(cat repo/.package_commit 2>/dev/null)" = "$(cat COMMIT)" ] || { echo "REFUSED: ./repo is not the package commit - run the package preflight (sha section) first"; exit 2; }
[ ! -e "$OUT" ] || { echo "REFUSED: $OUT exists - never repeated"; exit 2; }
mem=$(awk '/MemTotal/ {printf "%d", $2/1048576}' /proc/meminfo); [ "$mem" -ge 250 ] || { echo "REFUSED: ${mem} GiB memory (needs >= 256 GB)"; exit 2; }
disk=$(df -Pk "$PKG" | awk 'NR==2 {printf "%d", $4/1048576}'); [ "$disk" -ge 60 ] || { echo "REFUSED: ${disk} GiB free disk (needs >= 60)"; exit 2; }
[ -f "$LIC" ] && [ "$(stat -c %a "$LIC")" = 600 ] || { echo "REFUSED: licence file missing or not mode 600 at $LIC (existence and mode only)"; exit 2; }
MEMLIM=$(( mem * 8 / 10 ))
mkdir -p "$OUT"
log "FULLSIZE_PRESOLVE:start:$(now):commit=$(cat COMMIT):memory_gib=$mem:memlimit_gb=$MEMLIM:disk_free_gib=$disk:node=$(hostname)"
last_end=0
for spec in "F1 integrated integrated_2920_3h_unsolved.nc" "F2 no_new_xb no_new_xb_2920_3h_unsolved.nc"; do
  set -- $spec; rid=$1; sc=$2; net=$PKG/networks/$3; d=$OUT/$rid; mkdir -p "$d"
  t0=$(date +%s)
  ( cd repo && exec env -u GRB_LICENSE_FILE PYTHONHASHSEED=0 timeout -k 60 7200 /usr/bin/time -v "$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario "$sc" --output "$d" \
      --label SMOKE_TEST_ONLY --authorization "$AUTH; V3.1 optional full-size presolve $rid" --solver gurobi --solver-profile formal_barrier_1e6_t16 --scaling on --time-limit 864000 \
      --costs-table "$PKG/networks/integrated_costs_active_research.csv" --split-stage build > "$d/p1.log" 2> "$d/p1.err" ); ex=$?
  log "BUILD_$rid:exit=$ex:$(( $(date +%s) - t0 ))s:peak_gib=$(grep -h 'Maximum resident' "$d/p1.err" | awk '{printf "%.1f", $NF/1048576}'):lp_bytes=$(stat -c %s "$d/split/problem.lp" 2>/dev/null):$(now)"
  [ $ex = 0 ] && [ -f "$d/split/SPLIT_BUILD.json" ] || { log "STOP:$rid:build failed - no Gurobi call made"; log "FULLSIZE_PRESOLVE_RESULT:FAIL"; exit 3; }
  if [ $last_end -gt 0 ]; then while [ $(( $(date +%s) - last_end )) -lt $GAP ]; do sleep 10; done; fi
  [ "$(busy)" = 0 ] || { log "STOP:$rid:another solver process is running - no Gurobi call made"; log "FULLSIZE_PRESOLVE_RESULT:FAIL"; exit 3; }
  token_ok || { log "STOP:$rid:no TCP to the token server - no Gurobi call made"; log "FULLSIZE_PRESOLVE_RESULT:FAIL"; exit 3; }
  t1=$(date +%s); log "GUROBI_$rid:start:$(now)"
  ( cd repo && exec env GRB_LICENSE_FILE="$LIC" timeout -k 60 5400 /usr/bin/time -v "$PY" scripts_project/b4_split_solve.py --run-dir "$d" --probe-ordering-only --protect "MemLimit=$MEMLIM" > "$d/p2.log" 2> "$d/p2.err" ); ex=$?
  last_end=$(date +%s)
  v=$(verdict "$d/gurobi.linopy.log"); pl=$(grep -h "^Presolved:" "$d/gurobi.linopy.log" 2>/dev/null | tail -1)
  log "$rid:$v:${pl:-no Presolved line}:probe_exit=$ex:$(( last_end - t1 ))s:presolve_s=$(grep -h '^Presolve time:' "$d/gurobi.linopy.log" | tail -1 | awk '{print $3}'):peak_gib=$(grep -h 'Maximum resident' "$d/p2.err" | awk '{printf "%.1f", $NF/1048576}')"
  grep -viE "$SCRUB" "$d/gurobi.linopy.log" > "$d/GUROBI_LOG_SCRUBBED.txt" 2>/dev/null
  [ "$v" = PRESOLVE_PASSED ] && rm -f "$d/split/problem.lp"   # kept when not passed (for the reviewer)
done
grep -q '^F1:PRESOLVE_PASSED' "$ST" && grep -q '^F2:PRESOLVE_PASSED' "$ST" && log "FULLSIZE_PRESOLVE_RESULT:PASS" || log "FULLSIZE_PRESOLVE_RESULT:FAIL"
