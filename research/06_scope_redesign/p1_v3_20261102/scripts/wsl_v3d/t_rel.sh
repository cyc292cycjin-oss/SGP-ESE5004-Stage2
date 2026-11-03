#!/bin/bash
# V3 supplement 07: the test files touched by this supplement (daily aggregation, v3 runners with the new definition), with the v3 network and evaluation tests; no Gurobi (licence path set to a missing file).
# Refuses while a solve or another pytest is running (the runner stand-ins count s2_solve processes).
cd /home/jin/wt_v3_20261102 || exit 2
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[p]ytest')" = 0 ] || { echo "REFUSED: another solve or pytest is running"; exit 2; }
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj GRB_LICENSE_FILE=/nonexistent
S=$(date +%s)
/home/jin/miniforge3/envs/pypsa-earth/bin/python -m pytest -q -p no:cacheprovider tests/research/test_s1_adapter_daily_v5.py tests/research/test_v3_runners.py tests/research/test_v3.py "$@" 2>&1 | grep -vE "Warning|warn\(|^  |^$" | tail -15
echo "ELAPSED_S $(( $(date +%s) - S ))"
