#!/bin/bash
# W08: before any solve - V3.1 zero-slack gate on the three v4 networks (no solver; LP rows of the hooks on 3 snapshots) and the first-order estimate.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106; R=/home/jin/wt_v4_w08; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/builds
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
cd $R || exit 1
env -u GRB_LICENSE_FILE $PY scripts_project/zero_slack_check.py --repo . --out $W/evidence/ZERO_SLACK_CHECK_V4.json \
  --network v4_F1=integrated:$B/main/integrated/integrated_2920_3h_unsolved.nc --network v4_F2=no_new_xb:$B/main/no_new_xb/no_new_xb_2920_3h_unsolved.nc \
  --network v4iid_F1=integrated:$B/iid/integrated/integrated_2920_3h_unsolved.nc > /home/jin/v4w08/zero_slack.log 2>&1
echo "ZERO_SLACK_EXIT:$?"; tail -5 /home/jin/v4w08/zero_slack.log
cd $W && $PY scripts/w08_first_order.py 2>&1 | grep -v -iE "warn|INFO" | tail -8
