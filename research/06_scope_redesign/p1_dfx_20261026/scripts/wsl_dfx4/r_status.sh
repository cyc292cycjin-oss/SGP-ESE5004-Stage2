# DFX phase 4 (ON the instance, read-only): runner STATUS, last monitor lines, Gurobi log tail (licence lines filtered), processes, memory, disk
O=/root/autodl-tmp/dfx_v8/runs/dfx; S='license[i]d|registered[[:space:]]+to|wls(access|secret)|academic|licen[cs]e (file|key|id)'
echo "== $(TZ=Asia/Singapore date '+%F %T') SGT"
echo "== STATUS"; grep -viE "$S" $O/STATUS.txt 2>/dev/null | cut -c1-260 | tail -${1:-25}
for r in V1 V2; do [ -f $O/MONITOR_$r.csv ] && echo "== MONITOR_$r ($(($(wc -l < $O/MONITOR_$r.csv)-1)) rows): $(tail -1 $O/MONITOR_$r.csv | cut -c1-200)"; done
for r in V1 V2; do [ -f $O/$r/gurobi.linopy.log ] && { echo "== $r gurobi log tail"; grep -viE "$S" $O/$r/gurobi.linopy.log | tail -4 | cut -c1-140; }; done
echo "== processes"; ps -eo pid,etimes,rss,args | grep -E '[s]2_solve\.py|[r]un_dfx\.sh|[l]23_violation|[s]4o_c1|[m]12_allocation|[m]12_rhs_audit|[g]ates_v6|[p]ack_results' | awk '{printf "%s %ss %.1fGiB ", $1, $2, $3/1048576; for (i=4;i<=NF && i<9;i++) printf "%s ", $i; print ""}' | cut -c1-200
awk '$1=="anon" {printf "cgroup anon %.2f GiB\n", $2/1073741824}' /sys/fs/cgroup/memory.stat; df -h /root/autodl-tmp | tail -1
for f in STOP STOP_SAFE UNUSABLE POSTPROC_ERRORS; do [ -f $O/$f ] && echo "!! $f: $(head -c 300 $O/$f | tr '\n' ' ')"; done
ls $O/results_*.tar.gz* 2>/dev/null
