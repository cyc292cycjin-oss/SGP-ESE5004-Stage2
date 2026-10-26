#!/bin/bash
# DFX phase 4: wait (max 20 min, poll 20 s) until the latest preflight console log on the instance holds PREFLIGHT_EXIT, then print it (filtered).
set -u
source /home/jin/dfx4/ssh.sh
for i in $(seq 1 60); do
  if dfx_ssh 'grep -q "^PREFLIGHT_EXIT:" "$(ls -t /root/autodl-tmp/dfx_v8/PREFLIGHT_CONSOLE_*.log | head -1)"' 2>/dev/null; then
    dfx_run /home/jin/dfx4/r_preflight_result.sh; exit 0
  fi
  sleep 20
done
echo "PREFLIGHT_WAIT_TIMEOUT"; dfx_run /home/jin/dfx4/r_preflight_result.sh
