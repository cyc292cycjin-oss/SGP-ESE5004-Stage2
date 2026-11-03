#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_hpc; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; cd $W
env -u GRB_LICENSE_FILE timeout -k 30 600 $PY -m pytest tests/research/test_v3_units.py -q --no-header -p no:cacheprovider -k bunker 2>&1 | grep -vE "Warning|^\s*$|df\[|Use .df|See the caveats|chained" | head -50
