#!/bin/bash
# 56 时段回归前置核对（只读）：残留进程、可用内存与 Q18 门槛、令牌服务器 TCP 连通、worktree 已跟踪改动、HEAD
cd /home/jin/wt_v5_x20 || exit 1
echo "procs: $(ps -eo args= | grep -cE '[p]ytest|[s]2_solve\.py|[g]urobi_cl|[s]2_network\.py')"
awk '/MemAvailable|MemTotal/{printf "%s %d MiB\n", $1, $2/1024}' /proc/meminfo
AV=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo); echo "F1 gate needs 9545 MiB: $([ $AV -ge 9545 ] && echo OK || echo REFUSE); F2 gate needs 7946 MiB: $([ $AV -ge 7946 ] && echo OK || echo REFUSE)"
timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null && echo "token route OK" || echo "token route FAIL"
echo "tracked changes: $(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)"; echo "HEAD $(git rev-parse HEAD)"
[ -f /home/jin/gurobi.lic ] && echo "licence file present (not read)"
