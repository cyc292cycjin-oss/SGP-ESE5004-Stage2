#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W
$PY /home/jin/v3/x1b_p2.py | tail -1
bash /home/jin/v3/x1b_tab.sh | tail -3
cd scripts_project; $PY v3_data.py 2>&1 | tail -1; $PY d1_registry.py 2>&1 | tail -2 | cut -c1-160; cd ..
env -u GRB_LICENSE_FILE $PY -m pytest tests/research/test_v3.py -q --no-header -p no:cacheprovider -W ignore --tb=short 2>&1 | tail -22 | cut -c1-200
git status --short | cut -c1-100 | head -20
