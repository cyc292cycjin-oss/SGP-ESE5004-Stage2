#!/bin/bash
# DFX v3: P10 commit -> push -> sync the work folder -> final facts.
set -u
echo "== commit"; bash /home/jin/dfx3/commit.sh /home/jin/dfx3/msg_p10.txt 2>&1 | tail -3
echo "== push"; bash /home/jin/dfx3/push.sh
echo "== sync work folder"; bash /home/jin/dfx3/sync_work.sh | tail -3
echo "== final facts"; cd /home/jin/wt_dfx_v3_20261026 && git log --format="%h %cI %s" 55ab07c0..HEAD | cut -c1-90; git status --short | wc -l
du -sb /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3 /home/jin/wt_dfx_v3_20261026 /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026 | cut -f1 | paste -sd' '
echo "gurobi_or_solve_processes=$(ps -eo args= | grep -ciE '[g]urobi|[s]2_solve\.py')"
