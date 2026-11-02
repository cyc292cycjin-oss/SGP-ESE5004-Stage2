#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W/scripts_project && $PY v3_tables.py --v2-network $MAIN/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc --v2-table /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv --main $MAIN --out $W/research/06_scope_redesign/p1_v3_20261102 2>&1 | grep -vE "UserWarning|^\s+warn|PROJ:" | tail -50
echo TAB_DONE
