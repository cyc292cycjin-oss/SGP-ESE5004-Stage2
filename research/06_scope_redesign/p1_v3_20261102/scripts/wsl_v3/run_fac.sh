#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W/scripts_project && $PY v3_facility_shares.py --main $MAIN --dose /mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102/03_subnational/DOSE_V2.11.csv --gadm /home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/gadm 2>&1 | grep -vE "UserWarning|^\s+warn|PROJ:" | tail -50
echo FAC_DONE
