#!/bin/bash
# S4O-6 point 1 (supplement 01: the probe runs only because the CPU (8481C) differs from the 8470Q; r >= 0.5 to continue): start speed_probe.sh in tmux
# session s4o_probe after NOT_BEFORE (epoch: preflight licence token + 5 min), wait for it, print SPEED_PROBE.json essentials.
# The process check and the launch are SEPARATE ssh calls: the launch command line contains the script name, so a check in the same remote command
# line would match itself (first attempt 00:15:52 refused for that reason; nothing had started). Host and port from the calling environment only.
set -u
source /home/jin/s4o_ssh.sh
NOT_BEFORE=${1:?epoch}
while [ $(date +%s) -lt $NOT_BEFORE ]; do sleep 5; done
AUTH="S4O-6 (user authorisation 2026-10-19 ~22:00 SGT, decision 121 / S4O supplement 01): speed probe because the instance CPU 8481C differs from the 8470Q; r >= 0.5 to continue; one run, 30 min stop-loss, no retry"
chk=$(s4o_ssh "ps -eo cmd | grep -cE '[s]2_solve.py|[s]peed_probe.sh|[r]un_365x24h.sh'; tmux has-session -t s4o_probe 2>/dev/null && echo SESSION_EXISTS")
[ "$chk" = "0" ] || { echo "REFUSED: instance check: $chk"; exit 2; }
s4o_ssh "date '+PROBE_LAUNCH_AT %F %T'; tmux new -d -s s4o_probe \"cd /root/autodl-tmp/s4o_cloud && PY=/root/miniconda3/envs/pypsa-earth/bin/python GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash speed_probe.sh --auth '$AUTH' > /root/autodl-tmp/s4o_probe_console.txt 2>&1\"; sleep 10; tmux ls" || exit $?
for i in $(seq 1 210); do   # wait for the probe (<= 35 min)
  s4o_ssh "tmux has-session -t s4o_probe 2>/dev/null" || break
  sleep 10
done
date +%s > /home/jin/s4o_tmp/last_gurobi_env_end_epoch
s4o_ssh "D=\$(ls -d /root/autodl-tmp/s4o_cloud/probe/*/ | tail -1); echo PROBE_DIR \$D; cat \$D/STATUS.txt | grep -viE 'licen|academic|wls' | cut -c1-500; grep -E 'Barrier solved|Optimal objective' \$D/GUROBI_LOG_SCRUBBED.txt"
