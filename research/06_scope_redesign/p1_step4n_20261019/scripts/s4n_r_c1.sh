# S4N-2 point 1 (runs ON the instance via "ssh bash -s"; read-only; no host, port or licence content)
echo "== lscpu"
lscpu | grep -E '^(Model name|Architecture|CPU\(s\)|On-line CPU|Thread\(s\) per core|Core\(s\) per socket|Socket\(s\)|CPU MHz|CPU max MHz|CPU min MHz|L3 cache|NUMA node\(s\)|BogoMIPS|Flags)' | cut -c1-160
echo "== current MHz (per logical CPU, counted)"; grep MHz /proc/cpuinfo | awk '{printf "%d\n", $4/100}' | sort -n | uniq -c | awk '{printf "%s x ~%d00 MHz; ", $1, $2} END {print ""}'
echo "== nproc: $(nproc)"
echo "== cgroup"
if [ -r /sys/fs/cgroup/cpu.max ]; then
  echo "v2 cpu.max: $(cat /sys/fs/cgroup/cpu.max)"; echo "v2 memory.max: $(cat /sys/fs/cgroup/memory.max)"; echo "v2 memory.current: $(cat /sys/fs/cgroup/memory.current)"
  echo "v2 cpuset.cpus.effective: $(cat /sys/fs/cgroup/cpuset.cpus.effective 2>/dev/null)"
else
  echo "v1 cpu.cfs_quota_us / period: $(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null) / $(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null)"
  echo "v1 memory.limit_in_bytes: $(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null)"; echo "v1 memory.usage_in_bytes: $(cat /sys/fs/cgroup/memory/memory.usage_in_bytes 2>/dev/null)"
  echo "v1 cpuset.cpus: $(cat /sys/fs/cgroup/cpuset/cpuset.cpus 2>/dev/null)"
fi
echo "== free -g"; free -g
echo "== disk"; df -h /root/autodl-tmp / 2>&1
echo "== os"; grep PRETTY_NAME /etc/os-release; uname -r; date '+%F %T %Z'
echo "== container start (PID 1)"; ps -o lstart= -p 1
echo "== loadavg (may be host-wide)"; cat /proc/loadavg
echo "== tools"; for t in tmux rsync setsid; do command -v $t >/dev/null 2>&1 && echo "$t ok" || echo "$t MISSING"; done; [ -x /usr/bin/time ] && /usr/bin/time -v true >/dev/null 2>&1 && echo "/usr/bin/time ok" || echo "/usr/bin/time MISSING"
echo "== conda"; ls -d /root/miniconda3 2>/dev/null || echo "no /root/miniconda3"; ls /root/miniconda3/envs 2>/dev/null
echo "== /root/.gurobi (names only)"; ls -la /root/.gurobi 2>/dev/null | awk 'NR>1 {print $1, $3, $5, $NF}' || echo "none"
echo "== /root/autodl-tmp content"; ls /root/autodl-tmp 2>/dev/null | head -20
echo "== gpu"; nvidia-smi -L 2>/dev/null | sed 's/(UUID.*)//'
echo "== running python / gurobi"; pgrep -af 'python|gurobi' | grep -v pgrep | cut -c1-120 || true
