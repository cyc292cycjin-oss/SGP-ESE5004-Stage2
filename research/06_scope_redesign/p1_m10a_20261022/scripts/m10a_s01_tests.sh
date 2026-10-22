#!/bin/bash
# M10A supplement 01: reference check of the registered values, then tests/research/test_m10p_batch3.py, then the full tests/research
set -u
WT=/home/jin/wt_m10p_20261022; E=/home/jin/m10a_evidence; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; mkdir -p $E
cd $WT || exit 1
chmod 755 research/06_scope_redesign/p1_m10p_20261022/cloud_package/*.sh research/06_scope_redesign/p1_m10p_20261022/cloud_package/env/install_env.sh
for f in research/06_scope_redesign/p1_m10p_20261022/cloud_package/run_batch3.sh research/06_scope_redesign/p1_m10p_20261022/cloud_package/preflight.sh research/06_scope_redesign/p1_m10p_20261022/cloud_package/make_package.sh; do bash -n $f || { echo "SYNTAX ERROR $f"; exit 1; }; done
L=$E/S01_REFERENCES.txt
{ echo "remaining 21600 / 22500 references in the third-batch files (expect none except history notes):"
  grep -nE "21,?600|22,?500" research/06_scope_redesign/p1_m10p_20261022/cloud_package/*.sh research/06_scope_redesign/p1_m10p_20261022/RUN_PLAN.md tests/research/test_m10p_batch3.py scripts_project/m10_batch3_summary.py tests/research/fixtures/m10p_fake_pipeline.py
  echo "--- new values ---"; grep -nE "28,?800|30,?000" research/06_scope_redesign/p1_m10p_20261022/cloud_package/*.sh tests/research/test_m10p_batch3.py | head -20
  echo "--- thresholds ---"; grep -nE "NEED_MEM_GIB=|NEED_DISK_GB=" research/06_scope_redesign/p1_m10p_20261022/cloud_package/preflight.sh; } > $L 2>&1; cat $L
L=$E/TESTS_s01_m10p.log
echo "HEAD $(git rev-parse HEAD) dirty_tracked $(git status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ) mode=s01_m10p" > $L
env -u GRB_LICENSE_FILE timeout 2400 $PY -m pytest tests/research/test_m10p_batch3.py -q -p no:cacheprovider -ra >> $L 2>&1; echo "EXIT $?" >> $L
echo "END $(date -u +%FT%TZ)" >> $L; echo DONE >> $L
echo "----- s01_m10p -----"; grep -E "^(EXIT|HEAD|END|FAILED)|passed|failed|error" $L | tail -12
if grep -q "^EXIT 0" $L; then
  L=$E/TESTS_s01_full.log
  echo "HEAD $(git rev-parse HEAD) dirty_tracked $(git status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ) mode=s01_full" > $L
  env -u GRB_LICENSE_FILE timeout 3000 $PY -m pytest tests/research -q -p no:cacheprovider -ra >> $L 2>&1; echo "EXIT $?" >> $L
  echo "END $(date -u +%FT%TZ)" >> $L; echo DONE >> $L
  echo "----- s01_full -----"; grep -E "^(EXIT|HEAD|END|FAILED)|passed|failed|error" $L | tail -8
fi
echo S01_TESTS_DONE
