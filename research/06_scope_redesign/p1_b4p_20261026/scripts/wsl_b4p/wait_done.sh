#!/bin/bash
# wait (<= 9.5 min) for a solve folder's .done, then print its status lines and key receipt facts: bash wait_done.sh <tag>
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p; D=$R/solves/${1:?tag}
w=0; while [ ! -f "$D/.done" ] && [ $w -lt 570 ]; do sleep 10; w=$((w + 10)); done
[ -f "$D/.done" ] || { echo "NOT_DONE after ${w}s"; grep -E "_$1:" "$R/SOLVES_STATUS.txt" | tail -2 | cut -c1-300; ps -eo pid,etime,rss,args | grep -E "[s]2_solve|[b]4_split" | cut -c1-90; free -m | sed -n 2p; exit 1; }
grep -E "_$1:|_$1_" "$R/SOLVES_STATUS.txt" | cut -c1-420
[ -f "$D/gurobi.linopy.log" ] && grep -E "Presolved:|Presolve time|Ordering time|Dense cols|Free vars|AA. NZ|Factor NZ|Factor Ops|Barrier performed|Barrier solved|Optimal objective|Iteration limit|Sub-optimal" "$D/gurobi.linopy.log"
[ -f "$D/gurobi.linopy.log" ] && grep -E "^ +(0|10|20|24|25) " "$D/gurobi.linopy.log" | cut -c1-100
