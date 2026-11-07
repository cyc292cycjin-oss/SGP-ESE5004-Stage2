#!/bin/bash
# V31 W15 stage B 7.1: run one command under a memory watchdog (instruction 7.1: one network at a time, no Gurobi process, >= 8 GiB available).
#   bash w15b_memguard.sh <log file> <command ...>
# Refuses to start when a Gurobi / solve process runs or MemAvailable < 8 GiB; kills the command's process group when MemAvailable drops
# below 1 GiB (protects the shared WSL instance); logs the peak RSS of the process tree and the minimum MemAvailable.
set -u
LOG=${1:?log}; shift
avail_kb() { awk '/MemAvailable/ {print $2}' /proc/meminfo; }
nsolve=$(ps -eo cmd | grep -cE '[g]urobi_cl|[g]urobipy|[s]2_solve\.py|[b]4_split_solve')
a0=$(avail_kb)
echo "GUARD_START $(date -u +%FT%TZ) solve_procs=$nsolve mem_available_gib=$(awk -v a=$a0 'BEGIN{printf "%.2f", a/1048576}')" | tee -a "$LOG"
if [ "$nsolve" -gt 0 ] || [ "$a0" -lt 8388608 ]; then echo "GUARD_REFUSED: condition of instruction 7.1 not met" | tee -a "$LOG"; exit 4; fi
setsid "$@" >> "$LOG" 2>&1 &
pid=$!; peak=0; minav=$a0
while kill -0 $pid 2>/dev/null; do
  rss=$(ps -o rss= --ppid $pid 2>/dev/null | awk '{s+=$1} END {print s+0}'); r0=$(ps -o rss= -p $pid 2>/dev/null | awk '{print $1+0}'); rss=$((rss + r0))
  [ "$rss" -gt "$peak" ] && peak=$rss
  av=$(avail_kb); [ "$av" -lt "$minav" ] && minav=$av
  if [ "$av" -lt 1048576 ]; then echo "GUARD_KILL $(date -u +%FT%TZ) mem_available_kb=$av" | tee -a "$LOG"; kill -TERM -- -$pid 2>/dev/null; sleep 5; kill -KILL -- -$pid 2>/dev/null; fi
  sleep 2
done
wait $pid; rc=$?
echo "GUARD_END $(date -u +%FT%TZ) exit=$rc peak_rss_gib=$(awk -v a=$peak 'BEGIN{printf "%.2f", a/1048576}') min_mem_available_gib=$(awk -v a=$minav 'BEGIN{printf "%.2f", a/1048576}')" | tee -a "$LOG"
exit $rc
