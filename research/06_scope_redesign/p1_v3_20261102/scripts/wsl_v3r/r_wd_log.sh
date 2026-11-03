# V3 screening rerun (supplement 07) (ON the instance, read-only): watchdog log tail, its process, the mark, the licence presence (stat only), pack files
echo "== $(TZ=Asia/Singapore date '+%F %T') SGT"
tail -4 /root/autodl-tmp/v3_watchdog_dmax/watchdog.log | cut -c1-170
ps -eo pid,etimes,args | grep -E '[v]3s_watchdog' | cut -c1-100
echo "mark: $([ -e /root/autodl-tmp/v3_screen_dmax/RECOVERED_OK ] && echo present || echo absent); licence: $([ -e /root/.gurobi/gurobi.lic ] && echo present || echo absent); tmux: $(tmux ls 2>/dev/null | cut -d: -f1 | tr '\n' ' ')"
