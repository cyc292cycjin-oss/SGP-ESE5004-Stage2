#!/bin/bash
# runner regression after supplement 02: v3 tests, both runners with stand-ins, DFX demand file list. No solve may run beside it.
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; cd $W
env -u GRB_LICENSE_FILE timeout -k 30 1500 $PY -m pytest tests/research/test_v3.py tests/research/test_v3_runners.py tests/research/test_dfx_runner.py tests/research/test_b4p_batch4.py tests/research/test_dfx_demand.py -q --no-header -p no:cacheprovider --tb=short -W ignore 2>&1 | tail -30 | cut -c1-220
