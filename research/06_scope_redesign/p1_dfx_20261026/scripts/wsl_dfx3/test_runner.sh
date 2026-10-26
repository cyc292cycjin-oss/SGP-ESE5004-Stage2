#!/bin/bash
# DFX v3 F6: stand-in tests of run_dfx.sh / dfx_batch.py / preflight_dfx.sh (no solver). Must not run while a real solve is running.
set -u
WT=/home/jin/wt_dfx_v3_20261026; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
cd "$WT" || exit 1
n=$(ps -eo args= | grep -E '[s]2_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env ')
[ "$n" = 0 ] || { echo "REAL SOLVE RUNNING ($n) - stand-in tests not started"; exit 4; }
LOG=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/tests; mkdir -p $LOG
$PY -m pytest -q -p no:cacheprovider tests/research/test_dfx_runner.py "$@" > $LOG/runner.log 2>&1
rc=$?
grep -E "passed|failed|error|Error|assert" $LOG/runner.log | tail -40
echo "RUNNER_TESTS_EXIT=$rc"
