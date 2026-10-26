#!/bin/bash
# DFX v3: copy the light evidence files of phase 1-3 into the deliverable evidence/ folder (no network files, no LP arrays, no logs with licence lines).
set -u
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3; D=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026/evidence
PKG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_package_dfx
mkdir -p $D/smoke $D/dry_run $D/package $D/tests $D/leak_scan
cp $MAIN/smoke_v2/SMOKE_SUMMARY.json $MAIN/smoke_v2/STATUS.txt $D/smoke/
for sc in integrated disconnected; do cp $MAIN/smoke_v2/$sc/V6_ACCEPTANCE.json $D/smoke/${sc}_V6_ACCEPTANCE.json; cp $MAIN/smoke_v2/$sc/STOP_CLASS.json $D/smoke/${sc}_STOP_CLASS.json; cp $MAIN/smoke_v2/$sc/PRECISION.json $D/smoke/${sc}_PRECISION.json; grep -viE 'licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic' $MAIN/smoke_v2/$sc/gurobi.linopy.log > $D/smoke/${sc}_gurobi_log_scrubbed.txt; done
cp $MAIN/smoke_v2/BATCH_REFERENCE.json $MAIN/smoke_v2/M12_BENEFIT/BENEFIT.json $D/smoke/ 2>/dev/null
DR=${1:-dry_run_v8b}; cp $MAIN/$DR/DRY_RUN_DFX.json $MAIN/$DR/make_package.log $MAIN/$DR/preflight_local_sections.txt $MAIN/$DR/preflight_local_resources.txt $MAIN/$DR/refusals/REFUSALS.txt $D/dry_run/
for p in full trunc; do cp $MAIN/$DR/$p/STATUS.txt $D/dry_run/${p}_STATUS.txt; for r in V1 V2; do cp $MAIN/$DR/$p/$r/BUILD_CHECK.json $D/dry_run/${p}_${r}_BUILD_CHECK.json; done; done
cp $PKG/PACKAGE_MANIFEST.json $PKG/SHA256SUMS $PKG/BUILD_INPUT_CHANGES.json $PKG/COMMIT $D/package/
cp $MAIN/tests/subset.log $MAIN/tests/runner.log $MAIN/tests/affected.log $D/tests/ 2>/dev/null; [ -f $MAIN/tests/full.log ] && cp $MAIN/tests/full.log $D/tests/full.log
cp $MAIN/leak_scan/P6_LEAK_SCAN.json $D/leak_scan/ 2>/dev/null
cp $MAIN/equivalence/*.json $D/ 2>/dev/null
ls -R $D | head -60; du -sh $D
