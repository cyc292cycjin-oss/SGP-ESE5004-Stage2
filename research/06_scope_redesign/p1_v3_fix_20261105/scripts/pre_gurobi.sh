#!/bin/bash
# Pre-check before a local Gurobi call: TCP to the token server, no solver / pytest / build process, memory, disk. Read-only.
set -u
timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null && echo "TOKEN_TCP:ok" || echo "TOKEN_TCP:FAILED"
n=$(ps -eo args= | grep -E '[b]4_split_solve\.py|[s]2_solve\.py|[d]iag_build\.py|[g]urobi_cl|[p]ytest|[z]ero_slack_check\.py' | grep -vcE '^(/usr/bin/)?time |^env ')
echo "SOLVER_OR_TEST_PROCESSES:$n"
free -g | awk 'NR==2 {print "MEM_TOTAL_GIB:" $2 " AVAILABLE_GIB:" $7}'
df -h /home/jin | awk 'NR==2 {print "DISK_HOME_FREE:" $4}'
ls -l /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_diag_20261105/evidence/runs/F1_M01/MATH_PROBLEM.json /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_diag_20261105/evidence/runs/F2_M02/MATH_PROBLEM.json 2>&1 | awk '{print $NF, $5}'
nproc
