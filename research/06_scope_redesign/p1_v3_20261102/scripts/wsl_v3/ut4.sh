#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W; env -u GRB_LICENSE_FILE timeout -k 30 900 $PY -m pytest tests/research/test_v3.py tests/research/test_v3_runners.py tests/research/test_s4d_3.py -q --no-header -p no:cacheprovider --tb=short -W ignore 2>&1 | tail -40 | cut -c1-220
