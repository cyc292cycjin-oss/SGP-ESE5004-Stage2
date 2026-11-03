# V3 supplement 07 rerun, second power-on (no-card mode), ON the instance, read-only: time, uptime, GPU absence, the result packs and their SHA256 files (names / sizes),
# licence absence (stat only), solver / runner processes, tmux sessions, data disk. Nothing is created, moved or changed.
echo "== $(TZ=Asia/Singapore date '+%F %T') SGT | uptime $(uptime -p) | pid1 start $(TZ=Asia/Singapore ps -o lstart= -p 1)"
echo "== cgroup cpu.max $(cat /sys/fs/cgroup/cpu.max 2>/dev/null); memory.max $(cat /sys/fs/cgroup/memory.max 2>/dev/null)"
echo "== gpu: $(nvidia-smi -L 2>&1 | head -1 | cut -c1-60)"
R=/root/autodl-tmp/v3_screen_dmax/runs/dfx
echo "== packs"; ls -la $R/results_*.tar.gz* 2>&1 | awk '{print $5, $9}'
cat $R/results_full_final_20261103T160537Z.tar.gz.sha256 2>/dev/null | cut -c1-80
echo "== STATUS last line: $(tail -1 $R/STATUS.txt | cut -c1-80)"
echo "== /root/.gurobi: $([ -d /root/.gurobi ] && echo "$(ls -A /root/.gurobi | wc -l) entries" || echo 'no directory'); licence file: $([ -e /root/.gurobi/gurobi.lic ] && echo PRESENT || echo absent)"
echo "== processes: $(ps -eo args= | grep -cE '[s]2_solve\.py|[r]un_dfx\.sh|[g]urobi|[v]3s_watchdog')"
echo "== tmux: $(tmux ls 2>&1 | cut -d: -f1 | tr '\n' ' ')"
df -h /root/autodl-tmp | tail -1
