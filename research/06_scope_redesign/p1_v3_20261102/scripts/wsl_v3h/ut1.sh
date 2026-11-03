#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_hpc; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; cd $W
echo "toy-solve grep:"; grep -nE 'optimize\(|\.solve\(|linprog' tests/research/test_v3_units.py tests/research/test_v3.py tests/research/test_s1_adapter_daily_v5.py tests/research/test_m12_allocation.py tests/research/test_s4d_3.py | head
env -u GRB_LICENSE_FILE timeout -k 30 1500 $PY -m pytest tests/research/test_v3_units.py tests/research/test_v3.py tests/research/test_s1_adapter_daily_v5.py tests/research/test_m12_allocation.py tests/research/test_s4d_3.py -q --no-header -p no:cacheprovider 2>&1 | tail -25
