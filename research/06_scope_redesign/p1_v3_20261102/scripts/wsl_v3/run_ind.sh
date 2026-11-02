#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W/scripts_project && $PY v3_industry.py --chain-dir $MAIN/results_project/v3/chain_vn 2>&1 | grep -vE "UserWarning|^\s+warn" | tail -22
ls -la $W/research_inputs/industry_v3 | tail -12
cd $W && git status --short | grep -v "^??" | head
