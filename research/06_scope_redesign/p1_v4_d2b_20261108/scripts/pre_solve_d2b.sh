#!/bin/bash
# D2b section 5 / 6.1: static checks of the two D2b main networks (W08 / D1 C1-C6, C8 difference vs the D2a networks with the expected set of sections 2-4, C10
# overflow ledger = table), the V3.1 zero-slack gate (no solver; LP rows of the hooks on 3 snapshots), the alarm lines from the D2a smoke duals. Nothing is solved.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2b_20261108; R=/home/jin/wt_v4_d2b; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d2b/builds
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
mkdir -p /home/jin/v4d2b
echo "== static"; cd $W && $PY scripts/d2b_static.py 2>&1 | grep -v -iE 'warn|INFO:|PROJ' | cut -c1-900; echo "STATIC_EXIT:${PIPESTATUS[0]}"
echo "== zero slack"; cd $R || exit 1
env -u GRB_LICENSE_FILE $PY scripts_project/zero_slack_check.py --repo . --out $W/evidence/ZERO_SLACK_CHECK_D2B.json \
  --network v4d2b_F1=integrated:$B/main/integrated/integrated_2920_3h_unsolved.nc --network v4d2b_F2=no_new_xb:$B/main/no_new_xb/no_new_xb_2920_3h_unsolved.nc > /home/jin/v4d2b/zero_slack.log 2>&1
echo "ZERO_SLACK_EXIT:$?"; tail -4 /home/jin/v4d2b/zero_slack.log
$PY - <<'P'
import json
z = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2b_20261108/evidence/ZERO_SLACK_CHECK_D2B.json"))
for k, v in (z.get("networks") or z).items():
    if isinstance(v, dict) and "passed" in v:
        print(k, "passed:", v["passed"], "forcing rows:", v.get("zero_slack_forcing_rows"), "rows:", len(v.get("constraints", [])), "verdicts:", v.get("verdicts"), "hooks:", v.get("required_constraint_hooks"))
P
echo "== bounds"; cd $W && $PY scripts/d2b_bounds_pre.py 2>&1 | grep -v -iE 'warn|INFO:|PROJ'; echo "BOUNDS_EXIT:${PIPESTATUS[0]}"
( cd $B && sha256sum */*/*_unsolved.nc )
echo PRE_SOLVE_DONE
