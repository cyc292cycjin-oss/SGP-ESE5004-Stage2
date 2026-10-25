#!/bin/bash
# stop the queued C4-C8 chain before its Gurobi process starts (no call consumed); keep the process-1 output of c4 as a build measurement
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p
for p in $(ps -eo pid,args | grep -E "[c]hain_c4_c8|[s]olve2\.sh" | awk '{print $1}'); do kill -TERM "$p" 2>/dev/null; done
sleep 2
n=$(ps -eo args | grep -cE "[b]4_split_solve\.py|[s]2_solve\.py"); echo "solve processes after stop: $n"
echo "CHAIN_C4_C8_STOPPED_BEFORE_GUROBI:$(date -u +%FT%TZ):re-planned to the dense-column regime (N > 200); c4 process 1 kept as a build measurement" >> "$R/SOLVES_STATUS.txt"
[ -d "$R/solves/c4_int112_split_T16" ] && [ ! -f "$R/solves/c4_int112_split_T16/.call_start" ] && mv "$R/solves/c4_int112_split_T16" "$R/solves/p1only_int112_split_T16" && echo renamed
cat "$R/.calls_used"; ps -eo pid,args | grep -E "[c]hain|[s]olve2" | cut -c1-80
