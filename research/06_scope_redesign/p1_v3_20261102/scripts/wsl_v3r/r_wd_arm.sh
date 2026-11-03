# V3 screening rerun (supplement 07) (ON the instance; V3_SCREEN_UNATTENDED.md section 2): arm the watchdog in its own tmux session v3wd, after the tests have passed.
W=/root/autodl-tmp/v3_watchdog_dmax; S=$W/v3s_watchdog.sh
tmux has-session -t v3wd 2>/dev/null && { echo "REFUSED: tmux session v3wd exists"; exit 2; }
[ -f "$S" ] || { echo "REFUSED: script missing"; exit 2; }
bash $S --check
tmux new-session -d -s v3wd "bash $S >> $W/watchdog.log 2>&1"; echo "tmux exit=$?"
sleep 3
tmux ls | cut -d: -f1 | tr '\n' ' '; echo
ps -eo pid,etimes,args | grep -E '[v]3s_watchdog' | cut -c1-110
tail -3 $W/watchdog.log | cut -c1-170
