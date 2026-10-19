#!/bin/bash
# wait for the speed probe on the instance (STATUS.txt DONE in the probe folder), polling every 30 s with short ssh calls (tolerates short outages);
# max MAX_S seconds; prints the last Gurobi line on each poll to the scratchpad log and the final STATUS. Host / port from the calling environment.
source /home/jin/s4n_ssh.sh
D=${1:?probe dir}; MAX_S=${2:-2100}; t0=$(date +%s)
LOG=/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/1fa8f672-a3bf-4ccd-aa5c-a7620da1e9a5/scratchpad/s4n_probe_watch.log
while :; do
  out=$(s4n_ssh "grep -q '^DONE' $D/STATUS.txt 2>/dev/null && echo PROBE_DONE; tail -1 $D/solve/gurobi.linopy.log 2>/dev/null | cut -c1-110; pgrep -c -f s2_solve.py" 2>&1)
  echo "$(TZ=Asia/Singapore date '+%T') $(echo "$out" | tr '\n' ' ')" >> $LOG
  if echo "$out" | grep -q PROBE_DONE; then break; fi
  [ $(( $(date +%s) - t0 )) -ge "$MAX_S" ] && { echo "WAIT_TIMEOUT"; tail -3 $LOG; exit 1; }
  sleep 30
done
s4n_ssh "cat $D/STATUS.txt; echo ---; cat /root/autodl-tmp/s4n_probe_launch.txt | grep -v '^AUTH'; echo ---; grep -E 'Barrier solved|Barrier performed|Optimal objective|Sub-optimal|Presolved:|Optimize a model|Thread count|CPU model' $D/GUROBI_LOG_SCRUBBED.txt"
