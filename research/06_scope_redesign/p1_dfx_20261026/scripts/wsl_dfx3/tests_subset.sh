#!/bin/bash
# DFX v3: demand-related test subset (no Gurobi; none of the five toy-LP tests is in this subset). Usage: bash tests_subset.sh [extra pytest args]
set -u
WT=/home/jin/wt_dfx_v3_20261026
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
cd "$WT" || exit 1
LOG=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/tests; mkdir -p $LOG
$PY -m pytest -q -p no:cacheprovider tests/research/test_m08b_demand.py tests/research/test_dfx_demand.py tests/research/test_m08b_s01.py tests/research/test_m08b_heat.py \
  tests/research/test_s2b_supplement02.py tests/research/test_s3b_r1.py tests/research/test_s3b_r2.py tests/research/test_d1_registry.py tests/research/test_s3_ammonia_methanol.py \
  tests/research/test_demand_accounting.py "$@" > $LOG/subset.log 2>&1
rc=$?
tail -25 $LOG/subset.log
echo "SUBSET_EXIT=$rc"
