# V3 screening (ON the instance; V3_SCREEN_UNATTENDED.md section 3 step 2): write the mark RECOVERED_OK after both packs were verified locally, then show
# that the watchdog has seen it and exited (its poll interval may need a minute).
M=/root/autodl-tmp/v3_screen/RECOVERED_OK; W=/root/autodl-tmp/v3_watchdog
[ -f "$M" ] && echo "MARK_EXISTS" || { echo "$(TZ=Asia/Singapore date '+%F %T') SGT light and full pack SHA256 verified locally" > "$M"; echo "MARK_WRITTEN"; }
ls -l "$M" | cut -c1-120
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  grep -q MARK_FOUND $W/watchdog.log && break
  sleep 10
done
tail -4 $W/watchdog.log | cut -c1-170
ps -eo pid,etimes,args | grep -E '[v]3s_watchdog' | cut -c1-110 || true
tmux ls 2>/dev/null | cut -d: -f1 | tr '\n' ' '; echo
