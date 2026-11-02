#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W/scripts_project && /usr/bin/time -f "%e s %M KB" $PY v3_liquids_data.py --network $MAIN/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc --land /home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial/shapes/country_shapes.geojson 2>&1 | grep -vE "UserWarning|^\s+warn|PROJ:" | tail -36
echo LIQ_DONE
