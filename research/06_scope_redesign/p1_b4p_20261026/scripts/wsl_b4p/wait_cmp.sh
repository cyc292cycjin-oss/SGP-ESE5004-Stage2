#!/bin/bash
# wait (<= 9 min) for a solve folder's .done, then compare it with another: bash wait_cmp.sh <tagA> <tagB|abs path> <label>
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p
w=0; while [ ! -f "$R/solves/$1/.done" ] && [ $w -lt 540 ]; do sleep 10; w=$((w + 10)); done
[ -f "$R/solves/$1/.done" ] || { echo "NOT_DONE after ${w}s"; grep -E "_$1:" "$R/SOLVES_STATUS.txt" | tail -2 | cut -c1-300; exit 1; }
grep -E "P3_$1|END_$1" "$R/SOLVES_STATUS.txt" | cut -c1-400
bash /home/jin/b4p/cmp1.sh "$1" "$2" "$3"
