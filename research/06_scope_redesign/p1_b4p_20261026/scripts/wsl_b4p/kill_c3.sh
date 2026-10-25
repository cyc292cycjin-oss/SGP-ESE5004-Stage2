#!/bin/bash
# B4P: the 90 % memory rule - terminate the C3 measurement (single-process 112-snapshot T16 solve) whose RSS reached 10.5 GiB of the 10.95 GiB WSL
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p
pid=$(ps -eo pid,args | grep -E "[s]2_solve\.py" | grep -v "time -v" | awk '{print $1}' | head -1)
[ -n "$pid" ] || { echo "no s2_solve process"; exit 0; }
pg=$(ps -o pgid= -p "$pid" | tr -d ' ')
echo "MEMORY_RULE_KILL_c3_int112_current_T16:$(date -u +%FT%TZ):pid=$pid:pgid=$pg:rss_kb=$(ps -o rss= -p "$pid" | tr -d ' '):mem_available_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo) - WSL memory above 90 % (instruction section 1): measurement terminated by hand" >> "$R/SOLVES_STATUS.txt"
kill -TERM -- "-$pg"; sleep 10
if pgrep -g "$pg" > /dev/null; then kill -KILL -- "-$pg"; echo "KILL9_c3:$(date -u +%FT%TZ)" >> "$R/SOLVES_STATUS.txt"; fi
sleep 2; free -m | sed -n 2p; tail -3 "$R/solves/c3_int112_current_T16/gurobi.linopy.log" 2>/dev/null | cut -c1-150
grep -E "Presolved|Factor NZ|Factor Ops|Ordering time|Presolve time|Dense cols|Free vars|AA" "$R/solves/c3_int112_current_T16/gurobi.linopy.log" 2>/dev/null
