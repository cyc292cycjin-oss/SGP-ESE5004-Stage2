#!/bin/bash
# V3 screening rerun (supplement 07): wait (max 35 min, poll 30 s) until the install console log on the instance holds INSTALL_EXIT, then print the result. Local, read-only.
set -u
source /home/jin/v3r/ssh.sh
for i in $(seq 1 70); do
  if v3s_ssh 'grep -q "^INSTALL_EXIT:" /root/autodl-tmp/v3_screen_dmax/ENV_INSTALL_CONSOLE.log' 2>/dev/null; then
    v3s_run /home/jin/v3r/r_env_status.sh 14; exit 0
  fi
  sleep 30
done
echo "ENV_WAIT_TIMEOUT_35_MIN"; v3s_run /home/jin/v3r/r_env_status.sh 14
