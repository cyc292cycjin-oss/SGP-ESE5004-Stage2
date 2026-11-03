#!/bin/bash
# rerun the three test_s3_gates failures of the full suite with details (no Gurobi; not beside a solve or another pytest)
cd /home/jin/wt_v3_hpc
n=$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[p]ytest ')
[ "$n" = 0 ] || { echo "REFUSED: busy $n"; exit 4; }
export PYTHONHASHSEED=0
env -u GRB_LICENSE_FILE timeout 1500 /home/jin/miniforge3/envs/pypsa-earth/bin/python -m pytest tests/research/test_s3_gates.py -q --no-header -p no:cacheprovider -k "${1:-test_static_b_gates or test_b12}" -vv 2>&1 | grep -vE 'Warning|warnings.warn' | tail -${2:-80} | cut -c1-400
