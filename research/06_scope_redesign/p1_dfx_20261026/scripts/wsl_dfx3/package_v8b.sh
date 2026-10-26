#!/bin/bash
# DFX v3 F6.3 (second build): package v8 at the fixed commit (dfx_batch.py without the import-time side effect). The first build (commit 5405e477)
# is moved aside as cloud_package_dfx_superseded_5405e477 (never deleted); the new package takes the instruction's path. Then the local preflight
# on a scratch copy (licence / resources sections not run locally).
set -u
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026
DIST=$W/cloud_package_dfx; DRY=${1:-dry_run_v8b}
cd $WT || exit 1
echo "HEAD=$(git rev-parse --short HEAD) dirty_tracked=$(git status --porcelain --untracked-files=no | wc -l)"
[ "$(git status --porcelain --untracked-files=no | wc -l)" = 0 ] || { echo "tracked changes present - commit first"; exit 2; }
if [ -d $DIST ]; then old=$(cut -c1-8 $DIST/COMMIT); mv $DIST ${DIST}_superseded_$old && echo "first build moved aside: ${DIST}_superseded_$old"; fi
DRY_RUN_JSON=$MAIN/results_project/dfx_v3/$DRY/DRY_RUN_DFX.json bash research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/make_package_dfx.sh $MAIN/results_project/dfx_v3/builds_v2 $DIST > $MAIN/results_project/dfx_v3/$DRY/make_package.log 2>&1
rc=$?; tail -6 $MAIN/results_project/dfx_v3/$DRY/make_package.log; echo "MAKE_PACKAGE_EXIT=$rc"; [ $rc = 0 ] || exit $rc
cat $DIST/COMMIT; sha256sum $DIST/SHA256SUMS $DIST/PACKAGE_MANIFEST.json; ( cd $DIST && sha256sum -c --quiet SHA256SUMS && echo "SHA256SUMS all OK ($(wc -l < SHA256SUMS) files)" )
rm -rf /home/jin/dfx3/pkg_check; mkdir -p /home/jin/dfx3/pkg_check; cp -r $DIST/. /home/jin/dfx3/pkg_check/; cd /home/jin/dfx3/pkg_check || exit 1
env -u GRB_LICENSE_FILE -u CGROUP_ROOT PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python bash preflight_dfx.sh > $MAIN/results_project/dfx_v3/$DRY/preflight_local_sections.txt 2>&1; echo "PREFLIGHT_LOCAL_EXIT=$?"; grep -E "^==|OK|FAILED|all_equal|modules import|no 2920" $MAIN/results_project/dfx_v3/$DRY/preflight_local_sections.txt | grep -v Warning
env -u GRB_LICENSE_FILE -u CGROUP_ROOT PREFLIGHT_ONLY=resources PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python PREFLIGHT_DISK_PATH=/home/jin bash preflight_dfx.sh > $MAIN/results_project/dfx_v3/$DRY/preflight_local_resources.txt 2>&1; echo "PREFLIGHT_RESOURCES_LOCAL_EXIT=$? (expected 1 on this WSL)"
TRUNCATE=56 PREFLIGHT_ONLY=guards bash preflight_dfx.sh | grep -E "SET IN THIS SHELL|PREFLIGHT"
bash env/install_env.sh --check-mirrors | tail -1
