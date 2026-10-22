#!/bin/bash
# M10P supplement 01: the runner tests only (synthetic stand-ins; no solver, no Gurobi)
set -u
WT=/home/jin/wt_m10p_20261022; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $WT || exit 1
env -u GRB_LICENSE_FILE timeout 1800 $PY -m pytest tests/research/test_m10p_batch3.py tests/research/test_m08a_a7.py -q -p no:cacheprovider -ra -x --durations=8 2>&1 | tail -40
