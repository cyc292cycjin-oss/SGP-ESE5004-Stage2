# S4O-6 watch body (runs ON the instance via "ssh bash -s"; read-only; no licence content)
RUN=$(ls -d /root/autodl-tmp/s4o_cloud/runs/*/ 2>/dev/null | tail -1)
cut -c1-230 ${RUN}STATUS.txt 2>/dev/null
for f in ${RUN}MONITOR_*.csv; do [ -f "$f" ] && echo "$(basename $f): $(tail -1 $f | cut -c1-200)"; done
L=$(ls -t ${RUN}*/gurobi.linopy.log 2>/dev/null | head -1)
if [ -n "$L" ]; then
  echo "BARRIER_LAST ($(basename $(dirname $L))):"
  grep -E '^ *[0-9]+ +[-0-9.e+]+ +[-0-9.e+]+ ' "$L" | tail -3
  grep -E 'Barrier solved|Barrier performed|Sub-optimal|Optimal objective|Time limit' "$L" | grep -viE 'licen|academic|wls' | tail -2
fi
u=$(cat /sys/fs/cgroup/memory.current); l=$(cat /sys/fs/cgroup/memory.max); c=$(awk '/^inactive_file /{print $2}' /sys/fs/cgroup/memory.stat)
awk -v u=$u -v l=$l -v c=$c 'BEGIN {printf "CGROUP_MEM used %.1f GiB (excl. inactive file cache %.1f) of %.1f GiB, available %.1f GiB\n", u/2^30, (u-c)/2^30, l/2^30, (l-u+c)/2^30}'
df -h /root/autodl-tmp | tail -1 | awk '{print "DISK_FREE " $4}'
tmux ls 2>/dev/null | cut -c1-60
