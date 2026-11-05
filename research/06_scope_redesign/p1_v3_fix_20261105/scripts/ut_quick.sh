#!/bin/bash
# Quick unit tests of the V3.1 change (no Gurobi; test_s4c_3 holds one HiGHS toy LP). Usage: bash ut_quick.sh [pytest args...]
set -u
cd /home/jin/wt_v3_fix
export PYTHONHASHSEED=0
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
if [ $# -eq 0 ]; then set -- tests/research/test_v31_bunker_fix.py tests/research/test_s4c_3.py tests/research/test_v3_units.py; fi
timeout 1800 $PY -m pytest -q -p no:cacheprovider "$@" 2>&1 | tail -40
