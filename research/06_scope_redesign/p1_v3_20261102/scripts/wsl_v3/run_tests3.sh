#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/tests
cd $W; echo "commit $(git rev-parse --short HEAD) real solves $(ps -eo args= | grep -cE '[s]2_solve\.py')" > $O/full_final.txt
env -u GRB_LICENSE_FILE timeout -k 30 3000 $PY -m pytest tests/research -q --no-header -p no:cacheprovider --tb=line -W ignore >> $O/full_final.txt 2>&1
echo "exit=$?" >> $O/full_final.txt
head -1 $O/full_final.txt; tail -7 $O/full_final.txt | cut -c1-170
