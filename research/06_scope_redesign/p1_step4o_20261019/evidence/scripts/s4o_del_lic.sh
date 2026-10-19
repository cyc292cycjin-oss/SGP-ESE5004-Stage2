#!/bin/bash
# S4O-6 point 6 / supplement 02 section 4 point 2: confirm no solve / analysis process on the instance, then delete the licence file (shred -u) and
# verify; nothing else is deleted. Host and port from the calling command line environment only (separate ssh calls: check, then delete).
set -u
source /home/jin/s4o_ssh.sh
chk=$(s4o_ssh "ps -eo cmd | grep -cE '[s]2_solve.py|[s]peed_probe.sh|[r]un_365x24h.sh|[s]4o_c1_precision|[l]23_violation'; tmux ls 2>/dev/null | grep -c '^s4o'")
echo "PROCESS_CHECK (solve/analysis processes, s4o tmux sessions): $(echo $chk | tr '\n' ' ')"
[ "$(echo "$chk" | head -1)" = "0" ] || { echo "REFUSED: a solve or analysis process is running"; exit 2; }
s4o_ssh "shred -u /root/.gurobi/gurobi.lic && echo LICENCE_DELETED_AT \$(date '+%F %T'); ls -la /root/.gurobi | awk 'NR>1 {print \$1, \$NF}'; test -e /root/.gurobi/gurobi.lic && echo STILL_PRESENT || echo LICENCE_ABSENT"
