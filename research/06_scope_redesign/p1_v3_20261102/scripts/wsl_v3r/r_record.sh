# V3 screening rerun (supplement 07) (ON the instance, read-only): records for the report before shutdown: data-disk use, watchdog log, mark, licence folder entries, tmux sessions,
# related processes.
echo "== RECORD_TIME $(TZ=Asia/Singapore date '+%F %T') SGT"
echo "== df data disk (bytes)"; df -B1 /root/autodl-tmp | tail -1 | awk '{print "size="$2" used="$3" avail="$4" use="$5}'
echo "== du (bytes)"; for d in /root/autodl-tmp/v3_screen_dmax /root/autodl-tmp/v3_screen_dmax/runs /root/autodl-tmp/v3_screen_dmax/export /root/autodl-tmp/envs /root/autodl-tmp/conda_pkgs_cache /root/autodl-tmp/v3_watchdog_dmax; do
  [ -e "$d" ] && du -sb "$d" 2>/dev/null; done
ls -la /root/autodl-tmp/v3_screen_dmax/*.tar.gz* 2>/dev/null | awk '{print $5, $9}'
echo "== watchdog.log"; cat /root/autodl-tmp/v3_watchdog_dmax/watchdog.log
echo "== RECOVERED_OK"; cat /root/autodl-tmp/v3_screen_dmax/RECOVERED_OK
echo "== WATCHDOG_SHUTDOWN.txt present: $([ -e /root/autodl-tmp/v3_screen_dmax/WATCHDOG_SHUTDOWN.txt ] && echo yes || echo no)"
echo "== /root/.gurobi entries: $(ls -A /root/.gurobi | wc -l)"
echo "== tmux: $(tmux ls 2>/dev/null | cut -d: -f1 | tr '\n' ' ')"
echo "== related processes: $(ps -eo args= | grep -cE '[s]2_solve\.py|[r]un_dfx\.sh|[p]ack_results|[m]12_allocation|[g]ates_v6|[v]3s_watchdog')"
