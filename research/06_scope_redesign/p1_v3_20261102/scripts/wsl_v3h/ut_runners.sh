#!/bin/bash
# runner regression + V3 HPC stand-in tests (no solver, no Gurobi, no model network); must not run beside a real solve
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_hpc; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; cd $W
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py')" = 0 ] || { echo "REFUSED: a solve is running"; exit 4; }
echo "toy-solve grep:"; grep -nE 'optimize\(|\.solve\(|linprog' tests/research/test_v3_hpc_runner.py tests/research/test_b4p_batch4.py tests/research/test_hpr_two_jobs.py tests/research/test_v3_runners.py tests/research/test_b4p_paths.py tests/research/test_dfx_runner.py | head -5
env -u GRB_LICENSE_FILE timeout -k 30 2400 $PY -m pytest ${@:-tests/research/test_b4p_batch4.py tests/research/test_hpr_two_jobs.py tests/research/test_v3_runners.py tests/research/test_b4p_paths.py tests/research/test_dfx_runner.py} -q --no-header -p no:cacheprovider -x 2>&1 | tail -30
