#!/bin/bash
export PYTHONHASHSEED=0
cd /home/jin/wt_v3_20261102
env -u GRB_LICENSE_FILE timeout -k 30 400 /home/jin/miniforge3/envs/pypsa-earth/bin/python -m pytest tests/research/test_v3_runners.py -q --no-header -p no:cacheprovider --tb=short -W ignore 2>&1 | tail -8 | cut -c1-220
