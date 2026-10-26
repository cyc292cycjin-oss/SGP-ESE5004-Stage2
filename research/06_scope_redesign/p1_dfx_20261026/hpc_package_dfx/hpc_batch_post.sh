#!/bin/bash
# DFX phase 2 (PROPOSED, offline draft; NOT stand-in tested): PBS job body of dfx_batch_post.pbs - the batch-level steps after BOTH per-run jobs
# (hpc_run_one.sh F1 and F2) have ended: the batch's own C1 reference from F1 / F2 (s4o_c1_precision.py reference), regrade of both runs (C1 regrade,
# Owen dual-form regrade, GATES_V6 accept again, stop-class), M12 benefit (B6 = F2 - F1), the fourth-batch summary (b4_batch4.py summary, optionally
# with the third-batch export for the comparison), scrubbed exports and the light / full packs (pack_results.sh of the third batch). No licence.
# Reads: PBS_O_WORKDIR = package folder on scratch; RUN_DIR default $HPCTMP/dfx_hpc/runs/batch4_two; BATCH3_EXPORT (optional path with R1/, R2/).
set -u
: "${PBS_O_WORKDIR:?run under PBS (qsub)}"
PKG="$PBS_O_WORKDIR"; cd "$PKG" || exit 2
USER_NAME=${USER:-$(id -un)}; SCRATCH=${HPCTMP:-/hpctmp/$USER_NAME}/dfx_hpc
REPO=${REPO:-$HOME/dfx_hpc/repo}; PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}; NETS="$PKG/networks"
OUT=${RUN_DIR:-$SCRATCH/runs/batch4_two}; export TMPDIR="$SCRATCH/tmp"; mkdir -p "$OUT/export/batch" "$TMPDIR"; ST="$OUT/STATUS.txt"; export PYTHONHASHSEED=0
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }; log() { echo "$*" >> "$ST"; }
P() { ( cd "$REPO" && exec env -u GRB_LICENSE_FILE timeout -k 60 10800 /usr/bin/time -v "$PY" "$@" ); }
log "BATCH_POST_START:${PBS_JOBID:-?}:$(now)"
for rid in F1 F2; do [ -f "$OUT/$rid/.ended" ] || { log "BATCH_POST:not_ready:$rid has not ended:$(now)"; exit 2; }; done
if [ ! -f "$OUT/BATCH_REFERENCE.json" ]; then
  if [ -f "$OUT/F1/COUNTRY_COST_LEDGER.csv" ] && [ -f "$OUT/F2/COUNTRY_COST_LEDGER.csv" ]; then
    P scripts_project/s4o_c1_precision.py reference --integrated "$OUT/F1" --disconnected "$OUT/F2" --out "$OUT/BATCH_REFERENCE.json" > "$OUT/batch_reference.log" 2>&1; log "BATCH_REFERENCE:exit=$?:$(now)"
  else log "BATCH_REFERENCE:not_available:F1 / F2 ledgers missing (the runs keep the provisional default reference):$(now)"; fi
fi
if [ -f "$OUT/BATCH_REFERENCE.json" ]; then
  for rid in F1 F2; do
    d="$OUT/$rid"; sc=$([ $rid = F1 ] && echo integrated || echo disconnected); [ -f "$d/PRECISION.json" ] || continue
    [ -f "$d/V6_ACCEPTANCE.json" ] && cp "$d/V6_ACCEPTANCE.json" "$d/V6_ACCEPTANCE_PROVISIONAL.json"
    P scripts_project/s4o_c1_precision.py regrade --solve-dir "$d" --reference "$OUT/BATCH_REFERENCE.json" > "$d/c1_regrade.log" 2>&1; rc=$?
    [ -f "$d/m12_owen/OWEN.json" ] && P scripts_project/m12_rhs_audit.py regrade --owen "$d/m12_owen/OWEN.json" --precision "$d/PRECISION.json" --out "$d/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json" > "$d/m12_owen_regrade.log" 2>&1
    lab=$(P scripts_project/v5/gates_v6.py accept --solve-dir "$d" --build-receipt "$NETS/${sc}_BUILD_RECEIPT.json" --repo . 2> "$d/v6.err" | tail -1); echo "$lab" > "$d/.label"
    read -r cls act < <(P scripts_project/b4_batch4.py stop-class --dir "$d" 2> "$d/stop_class.err" | tail -1)
    log "REGRADE_$rid:exit=$rc:final=$lab:class=${cls:-unreadable}:action=${act:-stop}:$(now)"
    case "$lab" in ACCEPTED_LAYER1|ACCEPTED_LAYER2) ;; *) grep -qx "$rid" "$OUT/STOP" 2>/dev/null || echo "$rid" >> "$OUT/STOP";; esac
  done
fi
if [ -f "$OUT/F1/ALLOCATION.json" ] && [ -f "$OUT/F2/ALLOCATION.json" ]; then
  P scripts_project/m12_allocation.py benefit --repo . --integrated "$OUT/F1" --disconnected "$OUT/F2" --out "$OUT/M12_BENEFIT" > "$OUT/M12_BENEFIT.log" 2>&1; log "M12_BENEFIT:exit=$?:$(tail -1 "$OUT/M12_BENEFIT.log" 2>/dev/null | cut -c1-200)"
else log "M12_BENEFIT:not_computable:F1 / F2 allocations missing"; fi
b3=(); [ -n "${BATCH3_EXPORT:-}" ] && [ -d "$BATCH3_EXPORT/R1" ] && b3=(--batch3 "$BATCH3_EXPORT")
P scripts_project/b4_batch4.py summary --out-dir "$OUT" ${b3[@]+"${b3[@]}"} > "$OUT/summary.log" 2>&1; log "SUMMARY:exit=$?:$(tail -1 "$OUT/summary.log" | cut -c1-300)"
# exports (scrubbed; no LP / solution arrays, no raw solver log) + packs
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'
for rid in F1 F2; do
  d="$OUT/$rid"; e="$OUT/export/$rid"; mkdir -p "$e"
  for f in RUN.json SOLVE_RECEIPT.json V5_GATES.json INTERIOR_CHECKS.json BUNKER_ACCOUNT.json GUROBI_LOG_SCRUBBED.txt RESOURCE.jsonl CO2_FLOWS.json EMISSIONS_BY_COUNTRY.json CAPACITY_BY_TECH_COUNTRY.json \
           cross_border_flows.csv COUNTRY_COST_LEDGER.csv COUNTRY_COST_LEDGER_USD2020.csv COUNTRY_COST_LEDGER_DETAIL.csv LEDGER_IDENTITY.json NODAL_PRICES.csv DUALS_BY_CONSTRAINT.nc DUALS_INDEX.csv \
           COMPONENT_COST_BREAKDOWN.csv COMPONENT_COST_BREAKDOWN_SUMMARY.json costs_active_research.csv PRECISION.json PRECISION.md VIOLATIONS.json EXPORTS.json ALLOCATION.json ALLOCATION.csv ALLOCATION.md \
           ALLOCATION_LINES.csv V6_ACCEPTANCE.json V6_ACCEPTANCE_PROVISIONAL.json STOP_CLASS.json; do [ -f "$d/$f" ] && cp "$d/$f" "$e/"; done
  [ -d "$d/m12_owen" ] && { mkdir -p "$e/m12_owen"; cp "$d/m12_owen"/*.json "$d/m12_owen"/*.csv "$d/m12_owen"/*.md "$e/m12_owen/" 2>/dev/null; }
  [ -d "$d/split" ] && { mkdir -p "$e/split"; cp "$d/split"/*.json "$e/split/" 2>/dev/null; }
  for f in p1 p2 p3; do [ -f "$d/$f.log" ] && grep -viE "$SCRUB" "$d/$f.log" > "$e/${f}_log_scrubbed.txt"; done
  ls "$d"/*_solved.nc > /dev/null 2>&1 && cp "$d"/*_solved.nc "$e/"; [ -f "$OUT/MONITOR_$rid.csv" ] && cp "$OUT/MONITOR_$rid.csv" "$e/"
done
for f in STATUS.txt BASE_CHECK_F1.json BASE_CHECK_F2.json BATCH_REFERENCE.json BATCH4_SUMMARY.json BATCH4_SUMMARY.md STOP STOP_SAFE PBS_JOBS.txt; do [ -f "$OUT/$f" ] && cp "$OUT/$f" "$OUT/export/batch/"; done
[ -d "$OUT/M12_BENEFIT" ] && { mkdir -p "$OUT/export/batch/M12_BENEFIT"; cp -r "$OUT/M12_BENEFIT"/. "$OUT/export/batch/M12_BENEFIT/"; }
r=$(PY="$PY" bash "$PKG/pack_results.sh" "$OUT" final 2>&1 | tail -1); log "PACK:$r"
log "BATCH_POST_END:$(now)"; [ -f "$OUT/STOP" ] && exit 3 || exit 0
