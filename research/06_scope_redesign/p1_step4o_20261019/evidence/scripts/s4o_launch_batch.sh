#!/bin/bash
# S4O-6 point 4: wait until NOT_BEFORE (epoch, >= last Gurobi environment end + 5 min), check no solve on the instance, then start the batch in tmux
# session s4o: run_365x24h.sh --mode serial with the package defaults (profile A, runs disconnected,integrated_nze; the gap diagnostic only if the
# disconnected main is non-optimal), TimeLimit / wall-clock $2 / $3 (default 21,600 / 22,500 s), the S4N pilot integrated as the C1 reference (uploaded
# light-package files). The process check and the launch are separate ssh calls (a check in the launch command line would match itself).
# Host and port from the calling command line environment only.
set -u
source /home/jin/s4o_ssh.sh
NOT_BEFORE=${1:?epoch}; TL=${2:-21600}; WC=${3:-22500}
while [ $(date +%s) -lt $NOT_BEFORE ]; do sleep 5; done
AUTH="S4O-6 (user authorisation 2026-10-19 ~22:00 SGT, decision 121 / S4O supplement 01): serial disconnected STEPS and integrated NZE 365x24h, profile A, TimeLimit / wall $TL / $WC s, gap diagnostic only if the disconnected main is non-optimal; no retry, no parameter change"
chk=$(s4o_ssh "ps -eo cmd | grep -cE '[s]2_solve.py|[s]peed_probe.sh|[r]un_365x24h.sh'; tmux has-session -t s4o 2>/dev/null && echo SESSION_EXISTS")
[ "$chk" = "0" ] || { echo "REFUSED: instance check: $chk"; exit 2; }
s4o_ssh "echo DISK_FREE_GIB: \$(df -Pk /root/autodl-tmp | awk 'NR==2 {printf \"%.1f\", \$4/1048576}'); date '+LAUNCH_AT %F %T' | tee /root/autodl-tmp/s4o_batch_launch.txt
  tmux new -d -s s4o \"cd /root/autodl-tmp/s4o_cloud && GUROBI_TIME_LIMIT_S=$TL WALL_CAP_S=$WC PILOT_INTEGRATED=/root/autodl-tmp/s4n_pilot/integrated PILOT_PRECISION=/root/autodl-tmp/s4n_pilot/PILOT_PRECISION.json PY=/root/miniconda3/envs/pypsa-earth/bin/python GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash run_365x24h.sh --mode serial --auth '$AUTH' > /root/autodl-tmp/s4o_batch_console.txt 2>&1\"
  sleep 20; tmux ls; ls -d /root/autodl-tmp/s4o_cloud/runs/*; cat /root/autodl-tmp/s4o_cloud/runs/*/STATUS.txt | cut -c1-300" || exit $?
