#!/bin/bash
# V3 screening: after `shutdown`, wait and try to log in again; a refused / timed-out login (or a login that finds the system going down) means the
# instance is stopped. Host / port only from the environment; output scrubbed.
set -u
source /home/jin/v3s/ssh.sh
sleep "${1:-75}"
for i in 1 2; do
  out=$(v3s_ssh 'echo LOGIN_OK; uptime' 2>&1); rc=$?
  echo "$(TZ=Asia/Singapore date '+%T') SGT attempt $i: ssh rc=$rc: $(v3s_scrub "$out" | tr '\n' ' ' | cut -c1-200)"
  [ $rc != 0 ] && { echo "VERIFY: INSTANCE_UNREACHABLE (stopped)"; exit 0; }
  sleep 60
done
echo "VERIFY: INSTANCE_STILL_REACHABLE"; exit 1
