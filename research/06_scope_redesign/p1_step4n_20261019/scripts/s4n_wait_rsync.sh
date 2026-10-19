#!/bin/bash
# wait (max MAX_S s) until no local rsync upload to the instance is running
MAX_S=${1:-1500}; t0=$(date +%s)
while pgrep -f "rsync -e ssh" >/dev/null; do
  [ $(( $(date +%s) - t0 )) -ge "$MAX_S" ] && { echo "WAIT_TIMEOUT: $(pgrep -fc 'rsync -e ssh') rsync still running"; exit 1; }
  sleep 15
done
echo "NO_RSYNC_RUNNING after $(( $(date +%s) - t0 )) s"
