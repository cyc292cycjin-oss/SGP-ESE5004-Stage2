#!/bin/bash
# M10A tests, second pass: the four corrected tests first, then the full tests/research (toy LP tests allowed; GRB_LICENSE_FILE removed)
set -u
WT=/home/jin/wt_m10p_20261022; E=/home/jin/m10a_evidence; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $WT || exit 1
L=$E/TESTS_fix4.log
echo "HEAD $(git rev-parse HEAD) dirty_tracked $(git status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ) mode=fix4" > $L
env -u GRB_LICENSE_FILE timeout 900 $PY -m pytest tests/research/test_m10p_batch3.py -q -p no:cacheprovider -ra \
  -k "R1-extra0 or post_processing_crash_is_recorded or unregistered_limits or formal_run_refuses" >> $L 2>&1; echo "EXIT $?" >> $L
echo "END $(date -u +%FT%TZ)" >> $L; echo DONE >> $L
echo "----- fix4 -----"; grep -E "^(EXIT|HEAD|END)|passed|failed|error" $L | tail -8
if grep -q "^EXIT 0" $L; then
  L=$E/TESTS_full2.log
  echo "HEAD $(git rev-parse HEAD) dirty_tracked $(git status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ) mode=full2" > $L
  env -u GRB_LICENSE_FILE timeout 3000 $PY -m pytest tests/research -q -p no:cacheprovider -ra >> $L 2>&1; echo "EXIT $?" >> $L
  echo "END $(date -u +%FT%TZ)" >> $L; echo DONE >> $L
  echo "----- full2 -----"; grep -E "^(EXIT|HEAD|END)|passed|failed|error" $L | tail -8
fi
echo CHAIN2_DONE
