#!/bin/bash
# DFX v3 F6.3: build package v8 at the dry-run commit. The two post-commit edits of the HPC draft (leak-scan pattern obfuscation) are stashed for the
# build (they live under research/, outside the code archive) and restored afterwards; they are committed with the phase-3 evidence.
set -u
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
DIST=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_package_dfx
cd $WT || exit 1
echo "HEAD=$(git rev-parse --short HEAD) dirty_tracked=$(git status --porcelain --untracked-files=no | wc -l)"
git stash push -q -- research/06_scope_redesign/p1_dfx_20261026/hpc_package_dfx/hpc_preflight.sh research/06_scope_redesign/p1_dfx_20261026/hpc_package_dfx/make_hpc_package.sh && echo "stashed 2 files"
DRY_RUN_JSON=$MAIN/results_project/dfx_v3/dry_run_v8/DRY_RUN_DFX.json bash research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/make_package_dfx.sh $MAIN/results_project/dfx_v3/builds_v2 $DIST > $MAIN/results_project/dfx_v3/dry_run_v8/make_package.log 2>&1
rc=$?; cat $MAIN/results_project/dfx_v3/dry_run_v8/make_package.log | tail -12; echo "MAKE_PACKAGE_EXIT=$rc"
git stash pop -q && echo "stash restored: dirty_tracked=$(git status --porcelain --untracked-files=no | wc -l)"
[ $rc = 0 ] || exit $rc
ls -la $DIST $DIST/networks $DIST/env; cat $DIST/COMMIT; sha256sum $DIST/SHA256SUMS $DIST/PACKAGE_MANIFEST.json
( cd $DIST && sha256sum -c --quiet SHA256SUMS && echo "SHA256SUMS all OK ($(wc -l < SHA256SUMS) files)" )
# preflight on a scratch copy (the D: package stays pristine); licence and resources sections not run locally (licence = a Gurobi call; resources = instance)
rm -rf /home/jin/dfx3/pkg_check; mkdir -p /home/jin/dfx3/pkg_check; cp -r $DIST/. /home/jin/dfx3/pkg_check/
cd /home/jin/dfx3/pkg_check || exit 1
env -u GRB_LICENSE_FILE PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python bash preflight_dfx.sh > $MAIN/results_project/dfx_v3/dry_run_v8/preflight_local_sections.txt 2>&1; echo "PREFLIGHT_LOCAL_EXIT=$?"
grep -v -E "UserWarning|parser.parse|PROJ" $MAIN/results_project/dfx_v3/dry_run_v8/preflight_local_sections.txt
env -u GRB_LICENSE_FILE PREFLIGHT_ONLY=resources PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python PREFLIGHT_DISK_PATH=/home/jin bash preflight_dfx.sh > $MAIN/results_project/dfx_v3/dry_run_v8/preflight_local_resources.txt 2>&1; echo "PREFLIGHT_RESOURCES_LOCAL_EXIT=$? (expected to fail on the 16-core / 10 GiB WSL)"; tail -4 $MAIN/results_project/dfx_v3/dry_run_v8/preflight_local_resources.txt
# negative: a leftover switch is caught by the guards
TRUNCATE=56 PREFLIGHT_ONLY=guards bash preflight_dfx.sh | tail -2
