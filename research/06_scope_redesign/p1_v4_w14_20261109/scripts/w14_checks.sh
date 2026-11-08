#!/bin/bash
# W14 section 2.2-2.3 (no solver, no licence): static checks (scripts/w14_static.py: C1-C12, C6b, T56 cut and comparison with D2c), then the V3.1 zero-slack gate
# (scripts_project/zero_slack_check.py: LP rows of the hooks on 3 snapshots; "no new zero-margin row" = no zero-slack forcing row) on the two 2920x3h networks
# of the package and on the two 56-snapshot networks cut by the s2_solve.py --truncate 56 rule.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w14_20261109; R=/home/jin/wt_v4_w14; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w14/builds/main
T=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w14/trunc56
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[g]urobi_cl')" = 0 ] || { echo "REFUSED: a solve is running"; exit 2; }
echo "== static $(date -u +%FT%TZ)"
cd $W && env -u GRB_LICENSE_FILE /usr/bin/time -v $PY scripts/w14_static.py > logs/static.txt 2> logs/static.err; echo "STATIC_EXIT:$?"
grep -v -iE 'warn|INFO:|PROJ' logs/static.txt | cut -c1-1200; grep -E 'Maximum resident|Elapsed' logs/static.err
echo "== zero slack $(date -u +%FT%TZ)"
cd $R || exit 1
env -u GRB_LICENSE_FILE /usr/bin/time -v $PY scripts_project/zero_slack_check.py --repo . --out $W/evidence/ZERO_SLACK_CHECK_W14.json \
  --network w14_F1=integrated:$B/integrated/integrated_2920_3h_unsolved.nc --network w14_F2=no_new_xb:$B/no_new_xb/no_new_xb_2920_3h_unsolved.nc \
  --network w14_F1_56=integrated:$T/w14_integrated_56.nc --network w14_F2_56=no_new_xb:$T/w14_no_new_xb_56.nc > $W/logs/zero_slack.txt 2> $W/logs/zero_slack.err
echo "ZERO_SLACK_EXIT:$?"; grep -v -iE 'warn|INFO:|PROJ' $W/logs/zero_slack.txt | tail -8; grep -E 'Maximum resident|Elapsed' $W/logs/zero_slack.err
echo "CHECKS_DONE $(date -u +%FT%TZ)"
