#!/bin/bash
# V3 supplement 07: the daily-aggregation tests (synthetic networks, no solver); refuses while a solve or pytest is running
cd /home/jin/wt_v3_20261102 || exit 2
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[p]ytest')" = 0 ] || { echo "REFUSED: another solve or pytest is running"; exit 2; }
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj
S=$(date +%s)
/home/jin/miniforge3/envs/pypsa-earth/bin/python -m pytest -q -p no:cacheprovider tests/research/test_s1_adapter_daily_v5.py "$@" 2>&1 | tail -25
echo "ELAPSED_S $(( $(date +%s) - S ))"
git diff --stat | cat
