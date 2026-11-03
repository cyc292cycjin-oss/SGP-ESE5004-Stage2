#!/bin/bash
# V3 screening: wait (max 20 min, poll 20 s) until the latest preflight console log on the instance holds PREFLIGHT_EXIT, then print it (filtered).
set -u
source /home/jin/v3s/ssh.sh
for i in $(seq 1 60); do
  if v3s_ssh 'grep -q "^PREFLIGHT_EXIT:" "$(ls -t /root/autodl-tmp/v3_screen/PREFLIGHT_CONSOLE_*.log | head -1)"' 2>/dev/null; then
    v3s_run /home/jin/v3s/r_preflight_result.sh; exit 0
  fi
  sleep 20
done
echo "PREFLIGHT_WAIT_TIMEOUT"; v3s_run /home/jin/v3s/r_preflight_result.sh
