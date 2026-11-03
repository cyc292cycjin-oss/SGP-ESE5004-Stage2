#!/bin/bash
# the runner / job-body / submission stand-in tests with every "bash" resolved to the locally compiled bash 4.2 (PATH shim; no solver, no Gurobi, no model network)
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_hpc; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; S=/home/jin/v3h/bash42/shim; cd $W || exit 2
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[p]ytest ')" = 0 ] || { echo "REFUSED: a solve or pytest is running"; exit 4; }
mkdir -p $S; [ -e $S/bash ] || ln -s /home/jin/v3h/bash42/src/bash $S/bash
export PATH=$S:$PATH
echo "bash on PATH: $(command -v bash) -> $(bash --version | head -1)"
env -u GRB_LICENSE_FILE timeout -k 30 3600 $PY -m pytest ${@:-tests/research/test_v3_hpc_runner.py tests/research/test_hpr_two_jobs.py tests/research/test_b4p_batch4.py} -q --no-header -p no:cacheprovider -rf 2>&1 | tail -30
