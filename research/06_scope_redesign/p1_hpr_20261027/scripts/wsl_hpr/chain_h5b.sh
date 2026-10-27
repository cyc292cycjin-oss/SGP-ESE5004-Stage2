#!/bin/bash
# HPR: rebuild the package v9 at the current clean commit (the previous build kept as hpc_package_superseded_<commit8>), dry run, consistency, leak scan,
# evidence collection, then the FULL test suite (H-P5) - sequential, one machine, no solve.
set -u
WT=/home/jin/wt_hpr_20261027; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
R=$MAIN/results_project/hpr; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_hpr_20261027; DIST=$W/hpc_package; S=$R/CHAIN_H5B_STATUS.txt
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" | tee -a "$S"; }
cd "$WT" || exit 1
log START "commit=$(git rev-parse HEAD):dirty=$(git status --porcelain --untracked-files=no | wc -l)"
if [ -d "$DIST" ]; then old=$(cut -c1-8 "$DIST/COMMIT"); mv "$DIST" "$W/hpc_package_superseded_$old" && log SUPERSEDED "hpc_package_superseded_$old"; fi
t0=$(date +%s); bash /home/jin/hpr/package_v9.sh "$DIST" > "$R/package_v9_run.log" 2>&1; rc=$?; log PACKAGE "exit=$rc:seconds=$(( $(date +%s) - t0 ))"; tail -5 "$R/package_v9_run.log"
[ $rc = 0 ] || { log ABORT "package failed"; exit 2; }
t0=$(date +%s); bash /home/jin/hpr/dryrun.sh "$DIST" > "$R/dryrun_run.log" 2>&1; rc=$?; log DRYRUN "exit=$rc:seconds=$(( $(date +%s) - t0 ))"; tail -3 "$R/dry_run_v9/DRYRUN_STATUS.txt"
$PY research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/hpr_consistency.py --repo "$WT" --plan research/06_scope_redesign/p1_hpr_20261027/RUN_PLAN_HPC.md --runner "$DIST/run_batch4.sh" --preflight "$DIST/preflight.sh" --pbs "$DIST/pbs" --job "$DIST/hpc/hpr_job.sh" --out "$R/CONSISTENCY.json" > "$R/CONSISTENCY.txt" 2>&1; rc=$?
log CONSISTENCY "exit=$rc:$(tail -1 "$R/CONSISTENCY.txt")"
bash /home/jin/hpr/leak_scan.sh > "$R/leak_scan_run.log" 2>&1; rc=$?; log LEAK_SCAN "exit=$rc"
$PY - <<'P' | tee -a "$S"
import json, re
from pathlib import Path
pats = dict(l.split("=", 1) for l in Path("/home/jin/.dfx_leak_patterns").read_text().splitlines() if l and not l.startswith("#"))
r = json.load(open("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/hpr/leak_scan/HPR_LEAK_SCAN.json"))
print("LEAK_CLASSES: secret_values", r["n_secret_values"], "clean", r["clean"])
for t, v in r["targets"].items():
    for h in v["hits"]:
        txt = (Path(t) / h["file"]).read_text(errors="ignore"); cls = {k: len(re.findall(rx, txt, re.I | re.M)) for k, rx in pats.items()}
        print("  ", t.split("/")[-1] + "/" + h["file"], {k: n for k, n in cls.items() if n}, "values", h["value_hits"])
print("  commits_with_hits", {k: v["files"] for k, v in r["commits"].items() if v["value_hits"] or v["pattern_hits"]})
P
bash /home/jin/hpr/collect_evidence.sh > "$R/collect_evidence.log" 2>&1; log EVIDENCE "exit=$?:$(tail -2 "$R/collect_evidence.log" | tr '\n' ' ')"
log FULL_TESTS_START
bash /home/jin/hpr/tests_full.sh > "$R/tests_full_run.log" 2>&1; rc=$?; log FULL_TESTS "exit=$rc:$(grep -E 'passed|failed' "$R/tests/full.log" | tail -1)"
cp "$R/tests/full.log" "$R/tests/full_commit.txt" "$WT/research/06_scope_redesign/p1_hpr_20261027/evidence/tests/" 2>/dev/null
log DONE
