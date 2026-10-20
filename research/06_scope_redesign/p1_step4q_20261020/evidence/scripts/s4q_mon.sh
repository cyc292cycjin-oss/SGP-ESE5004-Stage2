#!/bin/bash
# S4Q-2 watcher: emits each new key line of the driver status and of every run STATUS.txt; exits after DRIVER_DONE.
declare -A seen
PAT='^(RUN_|RECEIPT_|PRECISION_|BATCH_REFERENCE|REGRADE_|NO_STOP|NO_GAP|STOP_|KILLED|KILL9|GROUP_SURVIVED|DISCONNECTED_MAIN|LICENCE|DONE|GAP_|END_|INVOKE_|DRIVER_|SOLVER_BUSY|PREFLIGHT_)'
while true; do
  for f in /home/jin/s4q_local/DRIVER_STATUS.txt /home/jin/s4q_local/pkg/runs/*/STATUS.txt; do
    [ -f "$f" ] || continue
    n=$(wc -l < "$f"); s=${seen[$f]:-0}
    if [ "$n" -gt "$s" ]; then
      tail -n +$((s + 1)) "$f" | head -n $((n - s)) | grep -E "$PAT" | cut -c1-200 | sed "s|^|$(basename $(dirname $f))/$(basename $f): |"
      seen[$f]=$n
    fi
  done
  grep -q '^DRIVER_DONE' /home/jin/s4q_local/DRIVER_STATUS.txt 2>/dev/null && { echo "WATCH_END driver done"; exit 0; }
  pgrep -f s4q_2_run.sh >/dev/null || { sleep 5; grep -q '^DRIVER_DONE' /home/jin/s4q_local/DRIVER_STATUS.txt || { echo "WATCH_END driver process gone without DRIVER_DONE"; exit 1; }; }
  sleep 15
done
