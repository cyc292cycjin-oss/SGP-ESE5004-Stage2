#!/bin/bash
# Section 4 check + section 2.2 premises on the four package networks (no solver). Writes evidence/ZERO_SLACK_CHECK_F1_F4.json.
set -u
cd /home/jin/wt_v3_fix
export PYTHONHASHSEED=0
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
NETS=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3/networks
EV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/evidence
mkdir -p "$EV"
echo "START $(date -u +%FT%TZ) head=$(git rev-parse HEAD) dirty=$(git status --porcelain --untracked-files=no | wc -l)" > "$EV/ZERO_SLACK_CHECK_F1_F4.log"
/usr/bin/time -v $PY scripts_project/zero_slack_check.py --repo . --out "$EV/ZERO_SLACK_CHECK_F1_F4.json" \
  --network F1=integrated:$NETS/integrated_2920_3h_unsolved.nc --network F2=no_new_xb:$NETS/no_new_xb_2920_3h_unsolved.nc \
  --network F3=integrated:$NETS/integrated_ev05_2920_3h_unsolved.nc --network F4=no_new_xb:$NETS/no_new_xb_ev05_2920_3h_unsolved.nc \
  >> "$EV/ZERO_SLACK_CHECK_F1_F4.log" 2> "$EV/ZERO_SLACK_CHECK_F1_F4.err"
echo "EXIT $? $(date -u +%FT%TZ)" >> "$EV/ZERO_SLACK_CHECK_F1_F4.log"
grep -E 'Maximum resident|Elapsed' "$EV/ZERO_SLACK_CHECK_F1_F4.err" >> "$EV/ZERO_SLACK_CHECK_F1_F4.log"
echo DONE >> "$EV/ZERO_SLACK_CHECK_F1_F4.log"
