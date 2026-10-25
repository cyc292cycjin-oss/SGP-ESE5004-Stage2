#!/bin/bash
# B4P: wait for the stand-in tests of the fork agent (pytest + fake s2_solve.py processes) to end, then C2 (56 int split, profile A, TL 1750;
# the first attempt was refused by the busy() check, no Gurobi call was made) and C3 (112 int, current single-process path, T16, TL 3300).
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p; ST=$R/SOLVES_STATUS.txt
w=0
while [ $w -lt 2400 ]; do
  n=$(ps -eo args= | grep -cE "[p]ytest|[s]2_solve\.py|[b]4_split_solve\.py|[m]10p_fake_pipeline")
  [ "$n" = 0 ] && break
  sleep 15; w=$((w + 15))
done
echo "WAIT_DONE:$(date -u +%FT%TZ):waited=${w}s" >> "$ST"
if [ -d "$R/solves/c2_int56_split_A" ] && [ ! -f "$R/solves/c2_int56_split_A/.call_start" ]; then rm -rf "$R/solves/c2_int56_split_A"; echo "C2_FOLDER_REMOVED:$(date -u +%FT%TZ):no Gurobi call had been made (refused attempt)" >> "$ST"; fi
MODE=split SC=integrated N=56 PROFILE=formal_barrier TAG=c2_int56_split_A TL=1750 bash /home/jin/b4p/solve.sh
MODE=current SC=integrated N=112 PROFILE=formal_barrier_1e6_t16 TAG=c3_int112_current_T16 TL=3300 bash /home/jin/b4p/solve.sh
echo "CHAIN_C2_C3_DONE:$(date -u +%FT%TZ)" >> "$ST"
