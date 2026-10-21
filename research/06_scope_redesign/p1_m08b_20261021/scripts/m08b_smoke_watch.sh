#!/bin/bash
# emit every new terminal-type line of the M08b smoke STATUS.txt; exit when DONE appears
ST=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke/STATUS.txt
seen=0
while true; do
  n=$(wc -l < $ST 2>/dev/null || echo 0)
  if [ "$n" -gt "$seen" ]; then
    tail -n +$((seen + 1)) $ST | grep -E --line-buffered 'END_|KILL|GAP_|SOLVE_|VIOLATIONS_|C1_|REGRADE|REFERENCE|V6_|BUSY|NO_LICENCE|DONE' | cut -c1-220
    seen=$n
  fi
  grep -q '^DONE' $ST 2>/dev/null && exit 0
  sleep 5
done
