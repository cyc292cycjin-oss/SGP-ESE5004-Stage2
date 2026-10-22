#!/bin/bash
# M10A tests, third pass: the timing-sensitive stop scenario twice, then the full tests/research once more (toy LP tests allowed; GRB_LICENSE_FILE removed)
set -u
WT=/home/jin/wt_m10p_20261022; E=/home/jin/m10a_evidence; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $WT || exit 1
L=$E/TESTS_stop2x.log
echo "HEAD $(git rev-parse HEAD) dirty_tracked $(git status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ) mode=stop2x" > $L
for i in 1 2; do
  env -u GRB_LICENSE_FILE timeout 900 $PY -m pytest tests/research/test_m10p_batch3.py -q -p no:cacheprovider -ra -k "stops_on_reference_runs_and_g2" >> $L 2>&1; echo "EXIT $?" >> $L
done
echo "END $(date -u +%FT%TZ)" >> $L; echo DONE >> $L
echo "----- stop2x -----"; grep -E "^(EXIT|HEAD|END)|passed|failed|error" $L | tail -8
if [ "$(grep -c '^EXIT 0' $L)" = 2 ]; then
  L=$E/TESTS_full3.log
  echo "HEAD $(git rev-parse HEAD) dirty_tracked $(git status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ) mode=full3" > $L
  env -u GRB_LICENSE_FILE timeout 3000 $PY -m pytest tests/research -q -p no:cacheprovider -ra >> $L 2>&1; echo "EXIT $?" >> $L
  echo "END $(date -u +%FT%TZ)" >> $L; echo DONE >> $L
  echo "----- full3 -----"; grep -E "^(EXIT|HEAD|END)|passed|failed|error" $L | tail -8
fi
echo CHAIN3_DONE
