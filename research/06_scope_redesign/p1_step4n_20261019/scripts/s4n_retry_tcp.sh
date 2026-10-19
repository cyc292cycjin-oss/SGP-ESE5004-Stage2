#!/bin/bash
# retry the TCP connection to the instance SSH port every 20 s for up to MAX_S seconds (no login). Host / port from the calling environment only.
: "${S4N_HOST:?}" "${S4N_PORT:?}"
MAX_S=${1:-180}; t0=$(date +%s)
while :; do
  if timeout 10 bash -c "</dev/tcp/$S4N_HOST/$S4N_PORT" 2>/dev/null; then echo "TCP_PORT_OPEN after $(( $(date +%s) - t0 )) s at $(TZ=Asia/Singapore date '+%T') SGT"; exit 0; fi
  [ $(( $(date +%s) - t0 )) -ge "$MAX_S" ] && { echo "TCP_PORT_STILL_CLOSED after $MAX_S s at $(TZ=Asia/Singapore date '+%T') SGT"; exit 1; }
  sleep 20
done
