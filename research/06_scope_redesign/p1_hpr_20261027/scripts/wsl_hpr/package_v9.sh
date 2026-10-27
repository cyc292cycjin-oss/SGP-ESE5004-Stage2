#!/bin/bash
# HPR H5.1: build the package v9 at the current (clean) commit into a NEW dist folder on D:, requiring the H4 drill record of this commit.
set -u
WT=/home/jin/wt_hpr_20261027; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
DIST=${1:-/mnt/d/ResearchWorkspaces/ASEAN/work/p1_hpr_20261027/hpc_package}; O=$MAIN/results_project/hpr/package; mkdir -p "$O"
cd "$WT" || exit 1
t0=$(date +%s)
H4_JSON=$MAIN/results_project/hpr/h4/H4_DRILL.json PY=$PY bash research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/make_hpc_package.sh "$MAIN/results_project/dfx_v3/builds_v2" "$DIST" > "$O/make_package.log" 2>&1; rc=$?
echo "PACKAGE_EXIT=$rc seconds=$(( $(date +%s) - t0 ))" | tee -a "$O/make_package.log"
tail -8 "$O/make_package.log"
[ $rc = 0 ] || exit $rc
( cd "$DIST" && sha256sum -c --quiet SHA256SUMS && echo "SHA256SUMS: all $(wc -l < SHA256SUMS) files OK" ) | tee "$O/sha256_check.txt"
ls "$DIST"/networks/ | tee -a "$O/make_package.log"
du -sb "$DIST" | tee -a "$O/make_package.log"
