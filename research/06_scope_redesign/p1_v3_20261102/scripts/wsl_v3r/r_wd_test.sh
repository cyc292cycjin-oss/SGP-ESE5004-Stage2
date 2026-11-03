# V3 screening rerun (supplement 07) (ON the instance; V3_SCREEN_UNATTENDED.md section 2 item 4): the two tests before arming. Live state first, then the whole flow on forged
# files in a temporary folder with --dry-run. The run folder and the licence are not touched (stat only); nothing is deleted.
W=/root/autodl-tmp/v3_watchdog_dmax; S=$W/v3s_watchdog.sh; T=$(mktemp -d /tmp/v3w_test.XXXXXX); LIC=/root/.gurobi/gurobi.lic
s0=$(stat -c '%a %s %Y' "$LIC"); r0=$(stat -c '%s %Y' /root/autodl-tmp/v3_screen_dmax/runs/dfx/STATUS.txt)
echo "== 1 live state (must be NOT_TERMINAL)"; L=$(bash $S --check); echo "$L"; case "$L" in *decision=NOT_TERMINAL*) t1=PASS;; *) t1=FAIL;; esac
export V3W_QUIET_S=3 V3W_POLL_S=1
scn() {   # $1 name, $2 expected last-line text, $3 wait, $4 file setup; extra arguments of the flow come from the environment
  local d=$T/$1 R=$T/$1/runs/dfx; mkdir -p "$R"; ( cd "$R" && eval "$4" )
  local out; out=$(V3W_RUN=$R V3W_MARK=$d/RECOVERED_OK V3W_REC=$d/WATCHDOG_SHUTDOWN.txt V3W_WAIT_S=$3 V3W_PROC_RE='[n]o_such_process_v3w' timeout 30 bash $S --dry-run 2>&1)
  local rc=$?; echo "-- $1: exit=$rc"; printf '%s\n' "$out" | grep -E 'TRIGGER|MARK_FOUND|NO_MARK|DRY_RUN' | sed "s#$T#<T>#g" | cut -c1-150
  if printf '%s\n' "$out" | grep -qF "$2" && [ "$rc" = 0 ] && [ ! -e "$d/WATCHDOG_SHUTDOWN.txt" ]; then echo "   PASS"; else echo "   FAIL (expected: $2)"; fails=$((fails + 1)); fi
}
fails=0
echo "== 2 forged terminal states (--dry-run)"
scn done_nomark 'terminal=DONE' 3 'echo "DONE:2026:unusable=none" > STATUS.txt'
scn halted_nomark 'terminal=HALTED' 3 'echo "HALTED:2026:x" > STATUS.txt'
scn stopsafe_file 'terminal=STOP_SAFE' 3 'echo "SOLVE_V1:x" > STATUS.txt; echo reason > STOP_SAFE'
scn stop_file 'terminal=STOP' 3 'echo "STOP_NOT_ACCEPTED:V1:g2:x" > STATUS.txt; echo V1 > STOP'
scn runner_gone 'terminal=RUNNER_GONE' 3 'echo "SOLVE_V1:x" > STATUS.txt'
scn mark_first 'MARK_FOUND' 3 'echo "DONE:2026:unusable=none" > STATUS.txt; touch ../../RECOVERED_OK'
d=$T/mark_late/runs/dfx; mkdir -p $d; ( sleep 5; touch $T/mark_late/RECOVERED_OK ) &
scn mark_late 'MARK_FOUND' 8 'echo "DONE:2026:unusable=none" > STATUS.txt'
wait
echo "== 3 forged terminal state with the real process pattern: the live runner must block the trigger for the whole 10 s"
R=$T/live_busy/runs/dfx; mkdir -p $R; echo "DONE:2026:unusable=none" > $R/STATUS.txt
out=$(V3W_RUN=$R V3W_MARK=$T/live_busy/RECOVERED_OK V3W_REC=$T/live_busy/W.txt V3W_WAIT_S=3 timeout 10 bash $S --dry-run 2>&1); rc=$?
echo "exit=$rc (124 = still waiting)"; printf '%s\n' "$out" | grep -cE 'TRIGGER|DRY_RUN' | sed 's/^/trigger lines: /'
if [ $rc = 124 ] && ! printf '%s\n' "$out" | grep -qE 'TRIGGER|DRY_RUN'; then t3=PASS; else t3=FAIL; fi
echo "== 4 nothing touched"
s1=$(stat -c '%a %s %Y' "$LIC"); r1=$(stat -c '%s' /root/autodl-tmp/v3_screen_dmax/runs/dfx/STATUS.txt)
[ "$s0" = "$s1" ] && echo "licence stat unchanged" || { echo "LICENCE STAT CHANGED"; t3=FAIL; }
echo "STATUS size $(echo "$r0" | cut -d' ' -f1) -> $r1 (the runner may append); WATCHDOG_SHUTDOWN.txt in the package folder: $(ls /root/autodl-tmp/v3_screen_dmax/WATCHDOG_SHUTDOWN.txt 2>/dev/null | wc -l); RECOVERED_OK: $(ls /root/autodl-tmp/v3_screen_dmax/RECOVERED_OK 2>/dev/null | wc -l)"
echo "RESULT:live=$t1:forged_fails=$fails:busy_blocks=$t3"
[ "$t1" = PASS ] && [ "$fails" = 0 ] && [ "$t3" = PASS ] && echo "WD_TESTS_ALL_PASS" || echo "WD_TESTS_FAILED"
