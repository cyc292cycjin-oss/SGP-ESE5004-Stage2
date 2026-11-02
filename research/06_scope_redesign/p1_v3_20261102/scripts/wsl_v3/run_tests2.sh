#!/bin/bash
# re-run of the failed tests of full.txt with no real solve running (the stand-in runners of the batch tests refuse to start beside a real s2_solve.py); then the four tests whose expectation followed V3
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/tests
cd $W
ps -eo args= | grep -cE '[s]2_solve\.py' | sed 's/^/real solves running: /'
grep -E '^FAILED ' $O/full.txt | sed -E 's/^FAILED ([^ ]+).*/\1/' | sort -u > $O/failed_ids.txt
wc -l < $O/failed_ids.txt
mapfile -t IDS < $O/failed_ids.txt
env -u GRB_LICENSE_FILE timeout -k 30 1500 $PY -m pytest "${IDS[@]}" -q --no-header -p no:cacheprovider --tb=line -W ignore > $O/rerun.txt 2>&1
echo "exit=$?" >> $O/rerun.txt
tail -14 $O/rerun.txt | cut -c1-210
