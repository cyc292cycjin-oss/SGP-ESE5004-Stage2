#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W; env -u GRB_LICENSE_FILE timeout -k 30 560 $PY -m pytest tests/research/test_v3_runners.py -q --no-header -p no:cacheprovider --tb=short -W ignore 2>&1 | tail -34 | cut -c1-210
