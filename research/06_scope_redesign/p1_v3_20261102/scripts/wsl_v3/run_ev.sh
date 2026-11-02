#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W/scripts_project && $PY v3_ev.py --ramp-dir /mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102/04_ev --nodes $MAIN/results_project/v3/phase1/V2_NODES.csv --id-tz $MAIN/results_project/v3/phase1/ID_NODE_TIMEZONE_PROPOSAL.csv 2>&1 | tail -30
echo EV_DONE
