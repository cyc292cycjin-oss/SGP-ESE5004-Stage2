#!/bin/bash
PY=$HOME/miniforge3/envs/pypsa-earth/bin/python
B=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_op
ls -la $B $B/* | head -40
$PY /home/jin/v3h/meta_probe.py $B/integrated/integrated_2920_3h_unsolved.nc
