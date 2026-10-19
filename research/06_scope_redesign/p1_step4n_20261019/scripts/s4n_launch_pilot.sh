#!/bin/bash
# S4N-4 launch: wait until NOT_BEFORE (epoch, >= probe end + 5 min), check no local Gurobi / no solve on the instance / disk, then start the pilot
# in tmux session s4n (TimeLimit / wall cap from the probe: 14,400 / 15,300 s). Host / port from the calling environment only.
set -u
source /home/jin/s4n_ssh.sh
NOT_BEFORE=${1:?epoch}; TL=${2:-14400}; WC=${3:-15300}
while [ $(date +%s) -lt $NOT_BEFORE ]; do sleep 5; done
bash /home/jin/s4n_local_nogurobi.sh | grep -q LOCAL_NO_GUROBI_PROCESS || { echo "REFUSED: local Gurobi process"; exit 2; }
s4n_ssh "ps -eo cmd | grep -qE '[s]2_solve.py|[s]peed_probe.sh|[r]un_365x24h.sh' && { echo 'REFUSED: solve running on the instance'; exit 2; }
  tmux has-session -t s4n 2>/dev/null && { echo 'REFUSED: tmux session s4n exists'; exit 2; }
  echo DISK_FREE_GIB: \$(df -Pk /root/autodl-tmp | awk 'NR==2 {printf \"%.1f\", \$4/1048576}')
  date '+LAUNCH_AT %F %T'
  tmux new -d -s s4n \"GUROBI_TIME_LIMIT_S=$TL WALL_CAP_S=$WC bash /root/autodl-tmp/s4n_pilot_launch.sh\"
  sleep 15; tmux ls; head -1 /root/autodl-tmp/s4n_pilot_launch.txt; ls -d /root/autodl-tmp/s4m_cloud/runs/*; cat /root/autodl-tmp/s4m_cloud/runs/*/STATUS.txt; ps -eo pid,cmd | grep -E '[s]2_solve' | cut -c1-100" || exit $?
