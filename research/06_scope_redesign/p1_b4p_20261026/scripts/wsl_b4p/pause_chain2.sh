#!/bin/bash
# pause chain v2 before C5's Gurobi process starts; keep C5's process-1 output
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p
for p in $(ps -eo pid,args | grep -E "[c]hain_c4_c8_v2|[s]olve3\.sh" | awk '{print $1}'); do kill -TERM "$p" 2>/dev/null; done
sleep 1
# the process-1 build of c5 may still run under setsid: let it finish or kill it (it is not a Gurobi call); kill to free memory now
for p in $(ps -eo pid,args | grep -E "[s]2_solve\.py" | awk '{print $1}'); do kill -TERM "$p" 2>/dev/null; done
sleep 3
echo "CHAIN_V2_PAUSED:$(date -u +%FT%TZ):after C4 process 2 exit 143 - cause under review" >> "$R/SOLVES_STATUS.txt"
echo "procs: $(ps -eo args | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py')"; cat "$R/.calls_used"
echo "--- status tail"; grep -E "c4_int224|MEMORY_RULE|KILL" "$R/SOLVES_STATUS.txt" | cut -c1-300
echo "--- c4 p2.err tail"; tail -c 1200 "$R/solves/c4_int224_probe25_T16/p2.err"
echo "--- c4 p2.log"; tail -c 600 "$R/solves/c4_int224_probe25_T16/p2.log"
echo "--- c4 gurobi log"; cat "$R/solves/c4_int224_probe25_T16/gurobi.linopy.log" | cut -c1-120 | tail -25
echo "--- c4 RESOURCE_SOLVE tail"; tail -3 "$R/solves/c4_int224_probe25_T16/split/RESOURCE_SOLVE.jsonl"
free -m | sed -n 2p
