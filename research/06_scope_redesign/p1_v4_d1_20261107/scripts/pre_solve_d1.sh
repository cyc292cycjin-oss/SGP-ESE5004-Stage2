#!/bin/bash
# D1 section 7.1 / 7.2: static checks of the two D1 networks (W08 C1-C7 + C8 / C9), V3.1 zero-slack gate (no solver; LP rows of the hooks on 3 snapshots),
# pre-solve bounds from the W08 smoke solutions. Nothing is solved.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d1_20261107; R=/home/jin/wt_v4_d1; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d1/builds
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
cd $W && $PY scripts/d1_static.py 2>&1 | grep -v -iE 'warn|INFO:' | tail -4; echo "STATIC_EXIT:${PIPESTATUS[0]}"
cd $W && $PY scripts/d1_static_extra.py 2>&1 | grep -v -iE 'warn|INFO:' | tail -6
cd $R || exit 1
env -u GRB_LICENSE_FILE $PY scripts_project/zero_slack_check.py --repo . --out $W/evidence/ZERO_SLACK_CHECK_D1.json \
  --network v4d1_F1=integrated:$B/main/integrated/integrated_2920_3h_unsolved.nc --network v4d1_F2=no_new_xb:$B/main/no_new_xb/no_new_xb_2920_3h_unsolved.nc > /home/jin/v4d1/zero_slack.log 2>&1
echo "ZERO_SLACK_EXIT:$?"; tail -4 /home/jin/v4d1/zero_slack.log
cd $W && $PY scripts/d1_bounds_pre.py 2>&1 | grep -v -iE 'warn|INFO:' | tail -4
( cd $B && sha256sum */*/*_unsolved.nc )
