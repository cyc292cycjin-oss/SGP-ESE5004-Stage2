#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W && $PY -m pytest tests/research/test_v3.py -q -x --no-header -p no:cacheprovider 2>&1 | tail -14 | cut -c1-170
grep -n "add_argument" scripts_project/s2_solve.py | cut -c1-175 | head -24
echo UT_DONE
