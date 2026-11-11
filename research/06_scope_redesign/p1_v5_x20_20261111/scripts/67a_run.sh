#!/bin/bash
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
free -g | head -2
$PY $D/scripts/67a_meta_peek.py $D/builds/v5main/integrated/integrated_2920_3h_unsolved.nc
