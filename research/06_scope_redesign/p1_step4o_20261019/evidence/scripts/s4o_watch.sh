#!/bin/bash
# S4O-6 watcher (local, read-only on the instance): every INTERVAL s append a summary to the scratchpad log; exit when STATUS.txt changes its number
# of result lines, when container memory available < 2 GiB, on DONE, on an ssh failure, or after MAX_MIN minutes (then re-armed).
# The remote body is the file s4o_r_watch.sh fed to "ssh bash -s" (a here-document inside $( ) was not recognised in the first version).
# usage: S4O_HOST=.. S4O_PORT=.. bash s4o_watch.sh [interval_s=900] [max_min=28]
source /home/jin/s4o_ssh.sh
INTERVAL=${1:-900}; MAX_MIN=${2:-28}
LOG=/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/1388eed3-1835-43dd-95c3-52dc53c6afe3/scratchpad/s4o_watch.log
t0=$(date +%s); n0=""
while :; do
  out=$(s4o_ssh "bash -s" < /home/jin/s4o_r_watch.sh 2>&1); rc=$?
  ts=$(TZ=Asia/Singapore date "+%F %T SGT")
  { echo "=== $ts (ssh rc $rc)"; echo "$out"; } >> "$LOG"
  if [ $rc -ne 0 ] || ! echo "$out" | grep -q "^CGROUP_MEM"; then echo "WATCH_EXIT:SSH_FAILED rc=$rc at $ts"; echo "$out" | tail -5; exit 0; fi
  n=$(echo "$out" | grep -cE "^(RUN_|KILLED_|KILL9_|RECEIPT_|PRECISION_|REGRADE_|BATCH_REFERENCE|PILOT_CONSISTENCY|STOP_|DONE|LICENCE STRING|GROUP_SURVIVED|DISCONNECTED_MAIN|GAP_)")
  [ -z "$n0" ] && n0=$n
  avail=$(echo "$out" | sed -n 's/.*available \([0-9.]*\) GiB.*/\1/p')
  if echo "$out" | grep -q "^DONE"; then echo "WATCH_EXIT:DONE at $ts"; echo "$out"; exit 0; fi
  if [ "$n" != "$n0" ]; then echo "WATCH_EXIT:STATUS_CHANGED at $ts"; echo "$out"; exit 0; fi
  if [ -n "$avail" ] && awk -v a=$avail 'BEGIN {exit !(a < 2)}'; then echo "WATCH_EXIT:LOW_MEMORY at $ts"; echo "$out"; exit 0; fi
  if [ $(( $(date +%s) - t0 )) -ge $(( MAX_MIN * 60 )) ]; then echo "WATCH_EXIT:PERIODIC at $ts"; echo "$out"; exit 0; fi
  sleep "$INTERVAL"
done
