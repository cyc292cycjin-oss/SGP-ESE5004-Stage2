#!/bin/bash
# DFX phase 4 watcher (local, read-only): every POLL_S seconds read the runner STATUS on the instance; print a line when it changes; exit when the
# batch has ended (DONE / HALTED) or a safe stop / not-accepted stop appears, or after MAX_H hours. Host / port only from the environment.
# Usage: wsl env DFX_HOST=.. DFX_PORT=.. bash /home/jin/dfx4/wait_end.sh [POLL_S=300] [MAX_S=50400]   (MAX_S: one watch segment; WATCH_END:segment)
set -u
source /home/jin/dfx4/ssh.sh
POLL_S=${1:-300}; MAX_S=${2:-50400}; t0=$(date +%s); last=""; fails=0
while [ $(( $(date +%s) - t0 )) -lt "$MAX_S" ]; do
  out=$(dfx_ssh 'tail -3 /root/autodl-tmp/dfx_v8/runs/dfx/STATUS.txt 2>/dev/null | cut -c1-220' 2>/dev/null); rc=$?
  if [ $rc != 0 ]; then fails=$((fails + 1)); echo "$(TZ=Asia/Singapore date '+%T') ssh failed (rc=$rc, $fails in a row)"; [ $fails -ge 6 ] && { echo "WATCH_END:ssh_failures"; exit 3; }; sleep "$POLL_S"; continue; fi
  fails=0
  cur=$(printf '%s' "$out" | tail -1)
  [ "$cur" != "$last" ] && { echo "$(TZ=Asia/Singapore date '+%T') SGT | $(dfx_scrub "$cur")"; last=$cur; }
  if printf '%s' "$out" | grep -qE '^(DONE|HALTED):|STOP_SAFE:|STOP_NOT_ACCEPTED:'; then echo "WATCH_END:$(printf '%s' "$out" | grep -oE '^(DONE|HALTED)|STOP_SAFE|STOP_NOT_ACCEPTED' | tail -1)"; exit 0; fi
  sleep "$POLL_S"
done
echo "WATCH_END:segment_${MAX_S}s"
dfx_run /home/jin/dfx4/r_status.sh 12
