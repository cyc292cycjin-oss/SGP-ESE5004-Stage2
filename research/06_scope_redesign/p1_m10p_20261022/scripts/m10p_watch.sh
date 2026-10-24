#!/bin/bash
# M10P dry-run watcher: emits new BUILD_CHECK / PARAM_CHECK / STOP / HALTED / DONE lines of the dry-run STATUS and exits when the runner has finished
S=${S:-/home/jin/m10p_dry/pkg/runs/batch3/STATUS.txt}; O=${O:-/home/jin/m10p_dry/build_only.out}; seen=0
while true; do
  n=$(wc -l < "$S" 2>/dev/null || echo 0)
  if [ "$n" -gt "$seen" ]; then
    sed -n "$((seen + 1)),${n}p" "$S" | grep -E "BUILD_CHECK|PARAM_CHECK|STOP|HALTED|DONE|Traceback|Killed" | cut -c1-220
    seen=$n
  fi
  grep -q RUNNER_EXIT "$O" 2>/dev/null && { grep RUNNER_EXIT "$O"; exit 0; }
  sleep 20
done
