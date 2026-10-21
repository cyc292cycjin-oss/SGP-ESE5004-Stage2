#!/bin/bash
set -u
cd /home/jin/wt_s4q_20261020
B=/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/db7f254d-3f62-4a49-ab56-2f4a5ec3d4f9/scratchpad/pr_s4q.md
gh pr view 40 --repo cyc292cycjin-oss/SGP-ESE5004-Stage2 --json number,headRefName,baseRefName,isDraft,state
gh pr create --repo cyc292cycjin-oss/SGP-ESE5004-Stage2 --draft --base codex/s4o-production-20261019 --head codex/s4q-tol-calibration-20261020 \
  --title "S4Q: BarConvTol 1e-6 candidate profile, level-1 calibration (local 56x3h, decision 123)" --body-file $B
