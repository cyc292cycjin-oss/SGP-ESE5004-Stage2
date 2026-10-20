#!/bin/bash
date
cat /home/jin/s4q_local/DRIVER_STATUS.txt
for r in /home/jin/s4q_local/pkg/runs/*/; do
  echo "== $r"; cut -c1-230 $r/STATUS.txt
  for f in $r/MONITOR_*.csv; do [ -f "$f" ] && echo "$(basename $f): $(tail -1 $f | cut -c1-240)"; done
done
ps -eo pid,etime,pcpu,rss,cmd | grep -E '[s]2_solve.py|[s]4o_c1|[l]23_viol' | cut -c1-150
