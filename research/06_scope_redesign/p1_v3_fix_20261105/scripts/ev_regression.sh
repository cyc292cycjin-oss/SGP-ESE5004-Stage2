#!/bin/bash
# Copy the light evidence of the 5.2 regression (drill run folder) into evidence/regression_56/ (logs filtered for licence-like lines); check the job outputs.
set -u
R=/home/jin/v3fix/drill_pkg_13ebce95/runs/smoke56_v31; EV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/evidence; O=$EV/regression_56
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic|accessid|secret'
mkdir -p "$O"
for f in SMOKE_STATUS.txt STATUS.txt PBS_JOBS.txt BATCH4_SUMMARY.json BATCH4_SUMMARY.md BATCH_REFERENCE.json; do [ -f "$R/$f" ] && grep -viE "$SCRUB" "$R/$f" > "$O/$f"; done
cp -r "$R/M12_BENEFIT" "$O/" 2>/dev/null
for rid in F1 F2; do
  e=$R/export/$rid; d=$O/$rid; mkdir -p "$d"
  for f in SOLVE_RECEIPT.json V5_GATES.json V6_ACCEPTANCE.json PRECISION.json BUNKER_ACCOUNT.json COUNTRY_COST_LEDGER.csv NODAL_PRICES.csv LEDGER_IDENTITY.json STOP_CLASS.json MATH_PROBLEM.json GUROBI_LOG_SCRUBBED.txt; do [ -f "$e/$f" ] && cp "$e/$f" "$d/"; done
  [ -f "$e/split/SPLIT_SOLVE.json" ] && cp "$e/split/SPLIT_SOLVE.json" "$d/"
  [ -f "$e/m12_owen/OWEN.json" ] && cp "$e/m12_owen/OWEN.json" "$d/"
done
ls "$R"/preflight_*.txt > /dev/null 2>&1 && for f in "$R"/preflight_*.txt; do grep -viE "$SCRUB" "$f" > "$O/$(basename "$f")"; done
echo "licence-like lines in the copied evidence and the job outputs:"
grep -rliE 'wls(acces[s]id|secre[t])|license[i]d|registere[d] to' "$O" "$EV"/drill_job_*.out 2>/dev/null || echo "(none)"   # pattern written so that this file itself does not match a key-name scan
du -sh "$O"; ls "$O" "$O/F1"
