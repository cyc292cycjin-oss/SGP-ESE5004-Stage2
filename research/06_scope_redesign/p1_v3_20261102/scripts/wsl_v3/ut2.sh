#!/bin/bash
export PYTHONHASHSEED=0
cd /home/jin/wt_v3_20261102
env -u GRB_LICENSE_FILE /home/jin/miniforge3/envs/pypsa-earth/bin/python -m pytest tests/research/test_v3.py -q --no-header -p no:cacheprovider -W ignore --tb=short 2>&1 | tail -6 | cut -c1-200
