#!/bin/bash
# V4 D1 (2026-11-07; decision 215 item 1; V4_D1_INSTRUCTION.md section 2 item 4): the status command of the v4 HPC package = a copy of
# research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/hpr_status.sh (SHA256 4fd0bd5c91f29fb3b990f129c138366eb9872d14f402d1c1c0dbf227821fd7e8, registered in the
# v3.1 package as hpc/hpr_status.sh; unchanged). Change, marked "V4 D1": per run the objective INCLUDING the constant term (SOLVE_RECEIPT.json objective = the value
# of the batch B6 and of REFERENCE_VALUES.json) next to the LP value (objective_lp = split/SPLIT_SOLVE.json objective) and the constant (receipt
# scaling.objective_constants.total_eur); before process 3 the objective is objective_lp + constant from the process-1 receipt; the RUN.json package commit.
# HPR step F (HPC_OPERATOR_GUIDE.md): ONE status command on the login node - job states, the current phase of F1 / F2, the latest barrier iteration,
# memory and time projections, stop lines, packs; nothing of the licence is printed (the Gurobi log lines are filtered).
#   bash hpc/hpr_status.sh [runs dir]      default: the formal run folder of pbs/HPC_PLAN.txt (RUNDIRS; v3.1 runs/batch5, smoke runs/smoke56_v31);
#                                          without that line runs/batch4 (also: runs/smoke56, runs/build_only_f1)
set -u
PKG="$(cd "$(dirname "$0")/.." && pwd)"; cd "$PKG" || exit 2
RD_FORMAL=runs/batch4; RDL=$(grep '^RUNDIRS|' pbs/HPC_PLAN.txt 2>/dev/null | tail -1); [ -z "$RDL" ] || IFS='|' read -r _ RD_FORMAL _ _ <<< "$RDL"
[[ "$RD_FORMAL" =~ ^runs/[A-Za-z0-9_][A-Za-z0-9_.-]*$ ]] || { echo "run folder '$RD_FORMAL' of pbs/HPC_PLAN.txt (RUNDIRS) is not runs/<name>"; exit 2; }
OUT=${1:-$RD_FORMAL}; PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}; SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'
echo "== $(date -u +%Y-%m-%dT%H:%M:%SZ) UTC  $(date) local ; package $(cat COMMIT 2>/dev/null | cut -c1-8) ; runs $OUT"
echo "== PBS jobs"; command -v qstat > /dev/null 2>&1 && qstat -u "${USER:-$(id -un)}" 2>/dev/null | tail -n +3 || echo "(qstat not available here)"
[ -f "$OUT/SUBMITTED.txt" ] && { echo "== submitted"; cat "$OUT/SUBMITTED.txt"; }
[ -f "$OUT/PBS_JOBS.txt" ] && { echo "== job records (last 8)"; tail -8 "$OUT/PBS_JOBS.txt" | cut -c1-220; }
if [ -f "$OUT/STATUS.txt" ]; then
  echo "== STATUS.txt (last 12 lines)"; tail -12 "$OUT/STATUS.txt" | cut -c1-220
  echo "== stop / error lines (contact the reviewer when any appears)"
  lines=$(grep -E "STOP_SAFE|STOP_NOT_ACCEPTED|UNUSABLE|HALTED|POSTPROC_ERROR|KILLED|MEMORY_STOP|PROJECTION_STOP|NOT_STARTED|WAIT_START.*STOP" "$OUT/STATUS.txt" | tail -8); [ -n "$lines" ] && echo "$lines" | cut -c1-220 || echo "(none)"
fi
{ [ -f "$OUT/STOP" ] || [ -f "$OUT/STOP_SAFE" ]; } && { echo "== STOP / STOP_SAFE files (the batch is halted - contact the reviewer)"; cat "$OUT/STOP" "$OUT/STOP_SAFE" 2>/dev/null | cut -c1-220; }
WMAX=$(grep '^LIMITS|' pbs/HPC_PLAN.txt 2>/dev/null | cut -d'|' -f5); WMAX=${WMAX:-7200}
# review item 6: a run holds the lock while it waits for its start slot (>= 330 s after every other Gurobi start / end, < 2 other Gurobi processes) - up to WAIT_START_MAX_S
[ -d "$OUT/.gurobi_start_lock" ] && echo "== start lock held by: $(cat "$OUT/.gurobi_start_lock/owner" 2>/dev/null) (V3 HPC, RUN_PLAN_HPC_V3 4: normal while that run waits for its start slot, up to $WMAX s = $((WMAX / 3600)) h; the second field is the epoch second it was taken; held longer, or a STOP_SAFE:START_LOCK line = contact the reviewer)"
for d in "$OUT"/F*/; do   # v2 F1 / F2; V3 HPC F1-F4
  d=${d%/}; rid=${d##*/}; [ -d "$d" ] || continue
  echo "== $rid"
  phase=not_started
  [ -f "$d/RUN.json" ] && phase=prepared; [ -f "$d/split/SPLIT_BUILD.json" ] && phase="process1_built"; [ -f "$d/.solve_start" ] && phase="process2_gurobi_running"
  [ -f "$d/.solve_end" ] && phase="process2_ended"; [ -f "$d/.ended" ] && phase="ended:$(cat "$d/.cond" 2>/dev/null)"; [ -f "$d/.label" ] && phase="$phase:label=$(cat "$d/.label")"
  echo "phase: $phase"
  if [ -f "$d/.solve_start" ]; then
    s=$(cat "$d/.solve_start"); e=$(cat "$d/.solve_end" 2>/dev/null || date +%s); el=$((e - s))
    wc=$(grep -m1 -oE "wall_cap=[0-9]+" "$OUT/STATUS.txt" | head -1 | cut -d= -f2); tl=$(grep -m1 -oE "time_limit=[0-9]+" "$OUT/STATUS.txt" | head -1 | cut -d= -f2)
    printf "gurobi elapsed: %d s (%.1f h); TimeLimit %s s; wall cap %s s; remaining to wall cap %d s\n" "$el" "$(awk -v e=$el 'BEGIN {print e/3600}')" "${tl:-?}" "${wc:-?}" "$(( ${wc:-0} - el ))"
  fi
  [ -f "$d/gurobi.linopy.log" ] && { echo "last barrier line: $(grep -E '^\s*[0-9]+\s+[-+]?[0-9]\.[0-9]+e' "$d/gurobi.linopy.log" | grep -viE "$SCRUB" | tail -1 | cut -c1-120)"; echo "iterations logged: $(grep -cE '^\s*[0-9]+\s+[-+]?[0-9]\.[0-9]+e' "$d/gurobi.linopy.log")"; grep -E "Barrier solved|Optimal objective|Barrier performed|time limit" "$d/gurobi.linopy.log" | grep -viE "$SCRUB" | tail -2 | cut -c1-120; }
  [ -f "$OUT/MONITOR_$rid.csv" ] && { echo "monitor (header / last): $(head -1 "$OUT/MONITOR_$rid.csv" | cut -c1-160)"; echo "                         $(tail -1 "$OUT/MONITOR_$rid.csv" | cut -c1-160)"; }
  [ -f "$OUT/PROJECTION_$rid.json" ] && [ -x "$PY" ] && "$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print('projection:', {k: r.get(k) for k in ('ready','exceeded','seconds_per_iteration_11_20','projected_total_s','limit_s')})" "$OUT/PROJECTION_$rid.json"
  [ -f "$d/split/SPLIT_SOLVE.json" ] && [ -x "$PY" ] && "$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print('split solve:', {k: r.get(k) for k in ('gurobi_status_name','termination_condition','bar_iter_count','objective','max_mem_used_gb','runtime_s')})" "$d/split/SPLIT_SOLVE.json"
  [ -x "$PY" ] && { [ -f "$d/SOLVE_RECEIPT.json" ] || [ -f "$d/split/SPLIT_SOLVE.json" ]; } && "$PY" - "$d" <<'P'
# V4 D1 (decision 215 item 1): objective incl. the constant term and the LP value side by side
import json, os, sys
d = sys.argv[1]
def rd(p):
    try:
        return json.load(open(os.path.join(d, p)))
    except Exception:
        return None
rec = rd("SOLVE_RECEIPT.json") or {}; sp = rd("split/SPLIT_SOLVE.json") or {}; run = rd("RUN.json") or {}
const = ((rec.get("scaling") or {}).get("objective_constants") or {}).get("total_eur")
lp = rec.get("objective_lp", sp.get("objective"))
obj = rec.get("objective") if "objective_lp" in rec else None
src = "SOLVE_RECEIPT.json (process 3)"
if obj is None and lp is not None:
    obj = lp + (const or 0.0); src = "objective_lp + constant of the process-1 receipt (process 3 pending)" if const is not None else "objective_lp (no constant recorded)"
f = lambda x: "-" if x is None else f"{x:,.2f} EUR"   # noqa: E731
print(f"objective incl. constant: {f(obj)} [{src}]; objective_lp: {f(lp)}; constant: {f(const)}; package_commit RUN.json {str(run.get('package_commit'))[:8]} / receipt {str(rec.get('package_commit'))[:8]}")
P
  [ -f "$d/PRECISION.json" ] && [ -x "$PY" ] && "$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); g=r.get('grade',{}); print('C1:', g.get('grade'), 'abc', int(bool(g.get('a'))), int(bool(g.get('b'))), int(bool(g.get('c'))))" "$d/PRECISION.json"
done
[ -f "$OUT/BATCH4_SUMMARY.md" ] && { echo "== BATCH4_SUMMARY.md (head)"; head -12 "$OUT/BATCH4_SUMMARY.md" | cut -c1-200; }
[ -f "$OUT/SMOKE_STATUS.txt" ] && { echo "== SMOKE_STATUS.txt"; cat "$OUT/SMOKE_STATUS.txt" | cut -c1-220; }
[ -f "$OUT/BUILD_ONLY_STATUS.txt" ] && { echo "== BUILD_ONLY_STATUS.txt"; cat "$OUT/BUILD_ONLY_STATUS.txt" | cut -c1-220; }
echo "== packs"; ls -l "$OUT"/results_*.tar.gz* 2>/dev/null || echo "(none yet)"
echo "== scratch"; df -h "$PKG" | tail -1; du -sh "$OUT" 2>/dev/null
echo "== when to contact the reviewer: any STOP_SAFE / STOP_NOT_ACCEPTED / UNUSABLE / HALTED / KILLED line above; a job in state E or gone without JOB_END; PROJECTION exceeded=True; PBS_JOBS.txt PREFLIGHT_FAILED; a 'remaining to wall cap' below 24 h with the barrier still running."
