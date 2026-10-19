#!/bin/bash
# wait until a local STATUS file has a DONE line (max MAX_S seconds), then print it without PROJ noise
S=${1:?status file}; MAX_S=${2:-900}
t0=$(date +%s)
until grep -q "^DONE" "$S" 2>/dev/null; do
  [ $(( $(date +%s) - t0 )) -ge "$MAX_S" ] && { echo "WAIT_TIMEOUT"; break; }
  sleep 10
done
grep -v PROJ "$S" | cut -c1-300
