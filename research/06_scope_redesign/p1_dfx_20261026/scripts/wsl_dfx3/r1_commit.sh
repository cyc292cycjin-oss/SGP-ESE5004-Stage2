#!/bin/bash
set -u
echo "== commit"; bash /home/jin/dfx3/commit.sh /home/jin/dfx3/msg_r1.txt 2>&1 | tail -2
echo "== push"; bash /home/jin/dfx3/push.sh | tail -4
echo "== sync"; bash /home/jin/dfx3/sync_work.sh | tail -1
echo "gurobi_or_solve_processes=$(ps -eo args= | grep -ciE '[g]urobi|[s]2_solve\.py')"
