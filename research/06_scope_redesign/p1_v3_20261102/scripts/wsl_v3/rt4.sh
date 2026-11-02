#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W; $PY /home/jin/v3/td_patch.py || exit 1
$PY -m pytest tests/research/test_dfx_demand.py -q --no-header -p no:cacheprovider --tb=short -W ignore 2>&1 | tail -2 | cut -c1-140
