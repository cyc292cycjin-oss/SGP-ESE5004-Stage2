#!/bin/bash
# V3 screening rerun (supplement 07) watcher (local, read-only): every POLL_S seconds read the runner STATUS on the instance; print a line when it changes; exit when the batch
# has ended (DONE / HALTED) or a safe stop / not-accepted stop appears, or after MAX_S seconds (one watch segment, about 30 min, then the status print).
# Usage: wsl env V3S_HOST=.. V3S_PORT=.. bash /home/jin/v3r/wait_end.sh [POLL_S=120] [MAX_S=1800]
set -u
source /home/jin/v3r/ssh.sh
POLL_S=${1:-120}; MAX_S=${2:-1800}; t0=$(date +%s); last=""; fails=0
while [ $(( $(date +%s) - t0 )) -lt "$MAX_S" ]; do
  out=$(v3s_ssh 'tail -4 /root/autodl-tmp/v3_screen_dmax/runs/dfx/STATUS.txt 2>/dev/null | cut -c1-220' 2>/dev/null); rc=$?
  if [ $rc != 0 ]; then fails=$((fails + 1)); echo "$(TZ=Asia/Singapore date '+%T') ssh failed (rc=$rc, $fails in a row)"; [ $fails -ge 6 ] && { echo "WATCH_END:ssh_failures"; exit 3; }; sleep "$POLL_S"; continue; fi
  fails=0
  cur=$(printf '%s' "$out" | tail -1)
  [ "$cur" != "$last" ] && { echo "$(TZ=Asia/Singapore date '+%T') SGT | $(v3s_scrub "$cur")"; last=$cur; }
  if printf '%s' "$out" | grep -qE '^(DONE|HALTED):|STOP_SAFE:|STOP_NOT_ACCEPTED:'; then echo "WATCH_END:$(printf '%s' "$out" | grep -oE '^(DONE|HALTED)|STOP_SAFE|STOP_NOT_ACCEPTED' | tail -1)"; v3s_run /home/jin/v3r/r_status.sh 30; exit 0; fi
  sleep "$POLL_S"
done
echo "WATCH_END:segment_${MAX_S}s"
v3s_run /home/jin/v3r/r_status.sh 12
