#!/bin/bash
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
E=$MAIN/results_project/v3hpc/evidence; mkdir -p $E
$PY /home/jin/v3h/chk_nets.py $MAIN/results_project/v3/builds_op/integrated/integrated_2920_3h_unsolved.nc $MAIN/results_project/v3hpc/trial_5e372e5d/integrated/integrated_2920_3h_unsolved.nc $E/TRIAL_5E372E5D_VS_REGISTERED.json
