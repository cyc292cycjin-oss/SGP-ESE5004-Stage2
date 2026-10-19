#!/bin/bash
# S4N-4 watcher (local, read-only on the instance): every INTERVAL s append a summary to the scratchpad log; exit when STATUS.txt changes its number
# of result lines (RUN_ / KILLED / RECEIPT_ / DONE / LICENCE), when container memory available < 2 GiB, or after MAX_MIN minutes.
# usage: S4N_HOST=.. S4N_PORT=.. bash s4n_watch.sh <remote run dir> [interval_s=900] [max_min=60]
source /home/jin/s4n_ssh.sh
RUN=${1:?remote run dir}; INTERVAL=${2:-900}; MAX_MIN=${3:-60}
LOG=/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/1fa8f672-a3bf-4ccd-aa5c-a7620da1e9a5/scratchpad/s4n_watch.log
t0=$(date +%s); n0=""
while :; do
  out=$(s4n_ssh "RUN=$RUN bash -s" 2>&1 <<'R'
cut -c1-220 $RUN/STATUS.txt 2>/dev/null
for f in $RUN/MONITOR_*.csv; do [ -f $f ] && echo "$(basename $f): $(tail -1 $f | cut -c1-260)"; done
L=$(ls $RUN/*/gurobi.linopy.log 2>/dev/null | tail -1)
[ -n "$L" ] && { echo "BARRIER_LAST:"; grep -E '^ *[0-9]+ +[-0-9.e+]+ +[-0-9.e+]+ ' $L | tail -3; grep -E 'Barrier|Sub-optimal|Optimal objective|Time limit' $L | grep -viE 'licen|academic|wls' | tail -3; }
if [ -r /sys/fs/cgroup/memory.max ]; then u=$(cat /sys/fs/cgroup/memory.current); l=$(cat /sys/fs/cgroup/memory.max); c=$(awk '/^inactive_file /{print $2}' /sys/fs/cgroup/memory.stat)
else u=$(cat /sys/fs/cgroup/memory/memory.usage_in_bytes); l=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes); c=$(awk '/^total_inactive_file /{print $2}' /sys/fs/cgroup/memory/memory.stat); fi
awk -v u=$u -v l=$l -v c=$c 'BEGIN {printf "CGROUP_MEM used %.1f GiB (excl. inactive file cache %.1f) of %.1f GiB, available %.1f GiB\n", u/2^30, (u-c)/2^30, l/2^30, (l-u+c)/2^30}'
ps -eo rss,comm | awk '/python/ {s+=$1} END {printf "PYTHON_RSS %.1f GiB\n", s/1048576}'
df -h /root/autodl-tmp | tail -1 | awk '{print "DISK_FREE " $4}'; tmux ls 2>/dev/null | cut -c1-60
R
)
  ts=$(TZ=Asia/Singapore date "+%F %T SGT")
  { echo "=== $ts"; echo "$out"; } >> "$LOG"
  n=$(echo "$out" | grep -cE "^(RUN_|KILLED_|KILL9_|RECEIPT_|DONE|LICENCE STRING|GROUP_SURVIVED)")
  [ -z "$n0" ] && n0=$n
  avail=$(echo "$out" | sed -n 's/.*available \([0-9.]*\) GiB.*/\1/p')
  if echo "$out" | grep -q "^DONE"; then echo "WATCH_EXIT:DONE at $ts"; echo "$out"; exit 0; fi
  if [ "$n" != "$n0" ]; then echo "WATCH_EXIT:STATUS_CHANGED at $ts"; echo "$out"; exit 0; fi
  if [ -n "$avail" ] && awk -v a=$avail 'BEGIN {exit !(a < 2)}'; then echo "WATCH_EXIT:LOW_MEMORY at $ts"; echo "$out"; exit 0; fi
  if [ $(( $(date +%s) - t0 )) -ge $(( MAX_MIN * 60 )) ]; then echo "WATCH_EXIT:PERIODIC at $ts"; echo "$out"; exit 0; fi
  sleep "$INTERVAL"
done
