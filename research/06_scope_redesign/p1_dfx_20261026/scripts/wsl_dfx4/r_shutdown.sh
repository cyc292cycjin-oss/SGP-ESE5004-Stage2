# DFX phase 4 (ON the instance; user authorisation, unattended supplement item 7): after the results are recovered, the licence deleted and the report
# pushed, stop the instance with `shutdown`. Refused if any solve / runner / post-processing process is still running or the licence is present.
echo "== SHUTDOWN_CHECK $(TZ=Asia/Singapore date '+%F %T') SGT"
n=$(ps -eo args= | grep -cE '[s]2_solve\.py|[r]un_dfx\.sh|[p]ack_results|[m]12_allocation|[g]ates_v6')
[ "$n" = 0 ] || { echo "REFUSED: $n related processes running"; exit 2; }
[ -e /root/.gurobi/gurobi.lic ] && { echo "REFUSED: licence present"; exit 2; }
echo "/root/.gurobi entries: $(ls -A /root/.gurobi | wc -l)"
sync
echo "SHUTDOWN_ISSUED $(TZ=Asia/Singapore date '+%F %T') SGT"
shutdown
echo "SHUTDOWN_EXIT:$?"
