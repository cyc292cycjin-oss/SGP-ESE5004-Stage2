#!/bin/bash
# M10P supplement 01 S01-2 (no cloud, no upload, no solve): deployment package v3 (code archive without research/, no 2920x3h network) at the
# committed head of the branch. The v2 package folder (commit eac6c3e0) is renamed to cloud_package_dist_v2_eac6c3e0/ (kept, never deleted).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022; WT=/home/jin/wt_m10p_20261022; E=$W/evidence/s01
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $WT || exit 1
[ "$(git branch --show-current)" = codex/m10-batch3-20261022 ] || { echo "WRONG BRANCH"; exit 2; }
V2=$W/cloud_package_dist_v2_eac6c3e0
if [ -d $W/cloud_package_dist ] && [ ! -e $V2 ]; then
  [ "$(cut -c1-8 $W/cloud_package_dist/COMMIT)" = eac6c3e0 ] || { echo "cloud_package_dist is not the v2 package"; exit 2; }
  mv $W/cloud_package_dist $V2 && echo "v2 package renamed to $V2 (kept)"
fi
mkdir -p $E/package
t0=$(date +%s)
bash research/06_scope_redesign/p1_m10p_20261022/cloud_package/make_package.sh $MAIN/m08b/builds_s01 $W/cloud_package_dist $MAIN/m10p/package_variants_s01 > $E/MAKE_PACKAGE.log 2>&1
echo "MAKE_PACKAGE_EXIT $? $(( $(date +%s) - t0 ))s" | tee -a $E/MAKE_PACKAGE.log
P=$W/cloud_package_dist
cp $P/BUILD_INPUT_CHANGES.json $P/COMMIT $P/EXPECTED_VARIANTS.json $P/PACKAGE_MANIFEST.json $P/SHA256SUMS $P/VARIANT_REPRODUCIBILITY.json $E/package/
{
  echo "package commit $(cat $P/COMMIT)"
  echo "files $(find $P -type f | wc -l)  total_bytes $(find $P -type f -printf '%s\n' | awk '{s+=$1} END {print s}')"
  echo "PACKAGE_MANIFEST.json sha256 $(sha256sum $P/PACKAGE_MANIFEST.json | cut -c1-64)  bytes $(stat -c %s $P/PACKAGE_MANIFEST.json)"
  echo "SHA256SUMS sha256 $(sha256sum $P/SHA256SUMS | cut -c1-64)"
  echo "code archive $(ls $P/code_*.tar.gz | xargs -n1 basename) $(stat -c %s $P/code_*.tar.gz) B; research/ files in it: $(tar tzf $P/code_*.tar.gz | grep -c '^research/.*[^/]$')"
  cmp -s $P/EXPECTED_VARIANTS.json $V2/EXPECTED_VARIANTS.json && echo "EXPECTED_VARIANTS.json identical to v2 (eac6c3e0)" || echo "EXPECTED_VARIANTS.json DIFFERS from v2"
  for f in $(cd $P && ls networks); do
    cmp -s $P/networks/$f $V2/networks/$f && echo "networks/$f identical to v2" || echo "networks/$f DIFFERS from v2"
  done
  echo "v2 networks not in v3: $(cd $V2/networks && ls | while read f; do [ -e $P/networks/$f ] || echo -n "$f "; done)"
  $PY -c "import json,sys; m=json.load(open(sys.argv[1])); print('upload_total_bytes_excluding_this_manifest', m['upload_total_bytes_excluding_this_manifest'], 'hours_at', m['upload']['hours_at'])" $P/PACKAGE_MANIFEST.json
} | tee $E/PACKAGE_SUMMARY.txt
