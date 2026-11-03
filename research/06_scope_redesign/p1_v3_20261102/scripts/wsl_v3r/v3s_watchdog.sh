#!/bin/bash
# V3 screening rerun (supplement 07), instance-side fail-safe (V3_SCREEN_UNATTENDED.md section 2). Runs in its own tmux session on the instance; reads the run folder only.
#   trigger (both): the runner STATUS is terminal (DONE, HALTED, STOP, STOP_SAFE) and for 15 min in a row no run_dfx.sh, solve or post-processing process
#     exists. No process for 15 min with a non-terminal STATUS is RUNNER_GONE: the runner was killed, handled as STOP_SAFE (section 1 of that file).
#   after the trigger: wait at most 4 h for the mark RECOVERED_OK (written by the local session after it has verified the packs); mark found -> exit, the
#     local session finishes the work.
#   no mark after 4 h: shred the licence, verify it is gone, write WATCHDOG_SHUTDOWN.txt, shutdown. The results stay on the data disk.
#   --check    one evaluation of the state; prints it and exits.
#   --dry-run  the whole flow; prints what it would do, never touches the licence, never shuts down. Only --check and --dry-run read the V3W_* overrides.
# No host, port or instance name in this file.
set -u
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MODE=run
case "${1:-}" in --check) MODE=check;; --dry-run) MODE=dry;; "") ;; *) echo "unknown argument $1"; exit 2;; esac
RUN=/root/autodl-tmp/v3_screen_dmax/runs/dfx; MARK=/root/autodl-tmp/v3_screen_dmax/RECOVERED_OK; REC=/root/autodl-tmp/v3_screen_dmax/WATCHDOG_SHUTDOWN.txt; LIC=/root/.gurobi/gurobi.lic
QUIET_S=900; WAIT_S=14400; POLL_S=60
PROC_RE='[r]un_dfx\.sh|[s]2_solve\.py|[l]23_violation_analysis|[s]4o_c1_precision|[m]12_allocation|[m]12_rhs_audit|[g]ates_v6|[d]fx_batch|[v]3_screen_tables|[p]ack_results'
if [ "$MODE" != run ]; then
  RUN=${V3W_RUN:-$RUN}; MARK=${V3W_MARK:-$MARK}; REC=${V3W_REC:-$REC}; QUIET_S=${V3W_QUIET_S:-$QUIET_S}; WAIT_S=${V3W_WAIT_S:-$WAIT_S}; POLL_S=${V3W_POLL_S:-$POLL_S}; PROC_RE=${V3W_PROC_RE:-$PROC_RE}
fi
log() { echo "$(TZ=Asia/Singapore date '+%F %T') SGT $*"; }
busy() {   # processes of the batch; a failing ps counts as busy
  local a; a=$(ps -eo args=) || { echo 1; return; }
  printf '%s\n' "$a" | grep -cE "$PROC_RE"
}
terminal() {   # the terminal state of the runner, empty when there is none
  local s="$RUN/STATUS.txt"
  if [ -f "$s" ]; then
    grep -qE '^DONE:' "$s" && { echo DONE; return; }
    grep -qE '^HALTED:' "$s" && { echo HALTED; return; }
    grep -qE '^STOP_SAFE:' "$s" && { echo STOP_SAFE; return; }
    grep -qE '^STOP_NOT_ACCEPTED:' "$s" && { echo STOP; return; }
  fi
  [ -f "$RUN/STOP_SAFE" ] && { echo STOP_SAFE; return; }
  [ -f "$RUN/STOP" ] && { echo STOP; return; }
  echo ""
}
finish() {   # $1 terminal state: no mark within the wait
  if [ "$MODE" = dry ]; then
    log "DRY_RUN:would shred -u $LIC; would write $REC (terminal $1); would shutdown"
    log "DRY_RUN_END:licence $([ -e "$LIC" ] && echo present || echo absent), nothing changed"; exit 0
  fi
  shred -u "$LIC" 2>/dev/null || rm -f "$LIC"
  local l; if [ -e "$LIC" ]; then l=STILL_PRESENT; else l=VERIFIED_ABSENT; fi
  { echo "time: $(TZ=Asia/Singapore date '+%F %T') SGT"; echo "terminal: $1"; echo "licence: $l $LIC"; echo "reason: no RECOVERED_OK within $WAIT_S s after the trigger"; echo "results: left on the data disk"; } > "$REC"
  sync; log "WATCHDOG_SHUTDOWN:terminal $1:licence $l"
  shutdown; log "SHUTDOWN_EXIT:$?"; exit 0
}
if [ "$MODE" = check ]; then
  st=$(terminal); n=$(busy)
  if [ -n "$st" ] && [ "$n" = 0 ]; then d=TERMINAL_QUIET_TIMER_WOULD_RUN; elif [ -n "$st" ]; then d=TERMINAL_BUT_BUSY; elif [ "$n" = 0 ]; then d=NO_PROCESS_NOT_TERMINAL; else d=NOT_TERMINAL; fi
  echo "CHECK:terminal=${st:-none}:busy=$n:decision=$d:shutdown=$(command -v shutdown || echo MISSING):shred=$(command -v shred || echo MISSING):licence=$([ -e "$LIC" ] && echo present || echo absent)"; exit 0
fi
log "WATCHDOG_START:mode=$MODE:quiet_s=$QUIET_S:wait_s=$WAIT_S:poll_s=$POLL_S:run=$RUN"
quiet=""
while :; do
  n=$(busy); now=$(date +%s)
  if [ "$n" != 0 ]; then
    [ -n "$quiet" ] && log "PROCESSES_BACK:$n"; quiet=""
  else
    [ -n "$quiet" ] || { quiet=$now; log "NO_PROCESS:quiet timer started (terminal=$(terminal))"; }
    [ $(( now - quiet )) -ge "$QUIET_S" ] && break
  fi
  sleep "$POLL_S"
done
st=$(terminal); [ -n "$st" ] || st=RUNNER_GONE
t0=$(date +%s); log "TRIGGER:terminal=$st:quiet >= $QUIET_S s:waiting up to $WAIT_S s for $MARK"
while [ $(( $(date +%s) - t0 )) -lt "$WAIT_S" ]; do
  [ -f "$MARK" ] && { log "MARK_FOUND:$MARK:watchdog exits, the local session finishes"; exit 0; }
  sleep "$POLL_S"
done
[ -f "$MARK" ] && { log "MARK_FOUND:$MARK:watchdog exits, the local session finishes"; exit 0; }
log "NO_MARK:after $WAIT_S s"
finish "$st"
