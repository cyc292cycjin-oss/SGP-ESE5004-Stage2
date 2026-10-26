#!/bin/bash
# DFX phase 4 pre-upload gate: the seven stand-in test files (third batch, B4P, DFX) in ONE pytest process; no Gurobi (licence removed from the env).
set -u
WT=/home/jin/wt_dfx_v3_20261026; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0
cd "$WT" || exit 1
echo "HEAD=$(git rev-parse --short HEAD) dirty=$(git status --porcelain --untracked-files=no | wc -l)"
n=$(ps -eo args= | grep -E '[s]2_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '); [ "$n" = 0 ] || { echo "REAL SOLVE RUNNING ($n)"; exit 4; }
LOG=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/tests; mkdir -p $LOG; t0=$(date +%s)
env -u GRB_LICENSE_FILE $PY -m pytest -q -p no:cacheprovider tests/research/test_dfx_runner.py tests/research/test_m10p_batch3.py tests/research/test_b4p_batch4.py tests/research/test_m10r_s1_modes.py tests/research/test_m10r_drill.py tests/research/test_b4p_paths.py tests/research/test_b4p_split.py > $LOG/pre_upload.log 2>&1
rc=$?; echo "PRE_UPLOAD_TESTS_EXIT=$rc seconds=$(( $(date +%s) - t0 ))"; grep -E "^(FAILED|ERROR)|passed|failed" $LOG/pre_upload.log | tail -20
