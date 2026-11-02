#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/tests
mkdir -p $O; cd $W
env -u GRB_LICENSE_FILE timeout -k 30 3000 $PY -m pytest tests/research -q --no-header -p no:cacheprovider -x --co -q 2>&1 | tail -3 | cut -c1-200
env -u GRB_LICENSE_FILE timeout -k 30 3000 $PY -m pytest tests/research -q --no-header -p no:cacheprovider --tb=line -W ignore > $O/full.txt 2>&1
echo "exit=$?" >> $O/full.txt
tail -40 $O/full.txt | cut -c1-200
