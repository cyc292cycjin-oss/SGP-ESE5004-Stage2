#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W; $PY /home/jin/v3/run_patch.py || exit 1
bash -n research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/run_dfx.sh && bash -n research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh && bash -n research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/hpr_job.sh && echo syntax_ok
env -u GRB_LICENSE_FILE timeout -k 30 1400 $PY -m pytest tests/research/test_dfx_runner.py tests/research/test_b4p_batch4.py tests/research/test_b4p_paths.py tests/research/test_hpr_two_jobs.py -q --no-header -p no:cacheprovider --tb=line -W ignore 2>&1 | tail -12 | cut -c1-200
