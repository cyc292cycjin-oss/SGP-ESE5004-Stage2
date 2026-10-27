#!/bin/bash
# HPR H4 compare -> H5.1 package v9 -> H5.3 dry run -> H-P3 consistency on the built package -> H-P8 leak scan. Sequential (one machine, one queue); no solve.
set -u
WT=/home/jin/wt_hpr_20261027; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
R=$MAIN/results_project/hpr; DIST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_hpr_20261027/hpc_package; S=$R/CHAIN_H5_STATUS.txt
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" | tee -a "$S"; }
cd "$WT" || exit 1
log START "commit=$(git rev-parse HEAD):dirty=$(git status --porcelain --untracked-files=no | wc -l)"
H4C=$(grep -m1 '^START:' "$R/h4/H4_DRILL_STATUS.txt" | sed 's/.*commit=\([0-9a-f]*\).*/\1/')   # the commit the drill ran at (not necessarily HEAD)
log H4_COMMIT "$H4C"
$PY /home/jin/hpr/h4_compare.py "$R/h4/runs/smoke56" "$MAIN/results_project/dfx_v3/smoke_v2" "$R/h4/H4_DRILL.json" "$H4C" > "$R/h4/H4_COMPARE.txt" 2>&1; rc=$?
cat "$R/h4/H4_COMPARE.txt" | cut -c1-400; log H4_COMPARE "exit=$rc"
[ $rc = 0 ] || { log ABORT "compare failed"; exit 2; }
grep -q '"bitwise_equal_to_dfx_smoke": true' "$R/h4/H4_DRILL.json" || { log ABORT "H4 not bitwise equal - stop condition"; exit 3; }
t0=$(date +%s); bash /home/jin/hpr/package_v9.sh "$DIST" > "$R/package_v9_run.log" 2>&1; rc=$?; log PACKAGE "exit=$rc:seconds=$(( $(date +%s) - t0 ))"; tail -6 "$R/package_v9_run.log"
[ $rc = 0 ] || { log ABORT "package failed"; exit 2; }
t0=$(date +%s); bash /home/jin/hpr/dryrun.sh "$DIST" > "$R/dryrun_run.log" 2>&1; rc=$?; log DRYRUN "exit=$rc:seconds=$(( $(date +%s) - t0 ))"; tail -4 "$R/dry_run_v9/DRYRUN_STATUS.txt"
mkdir -p "$R/consistency"
$PY research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/hpr_consistency.py --repo "$WT" --plan research/06_scope_redesign/p1_hpr_20261027/RUN_PLAN_HPC.md --runner "$DIST/run_batch4.sh" --preflight "$DIST/preflight.sh" --pbs "$DIST/pbs" --job "$DIST/hpc/hpr_job.sh" --out "$R/CONSISTENCY.json" > "$R/CONSISTENCY.txt" 2>&1; rc=$?
log CONSISTENCY "exit=$rc:$(tail -1 "$R/CONSISTENCY.txt")"
bash /home/jin/hpr/leak_scan.sh > "$R/leak_scan_run.log" 2>&1; rc=$?; log LEAK_SCAN "exit=$rc"; head -40 "$R/leak_scan_run.log" | cut -c1-300
log DONE
