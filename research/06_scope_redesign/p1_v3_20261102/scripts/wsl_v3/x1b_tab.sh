#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W
$PY scripts_project/v3_dedicated_lines.py --network $M/results_project/v3/builds/integrated/integrated_365_24h_unsolved.nc 2>&1 | grep -v PROJ | cut -c1-200
