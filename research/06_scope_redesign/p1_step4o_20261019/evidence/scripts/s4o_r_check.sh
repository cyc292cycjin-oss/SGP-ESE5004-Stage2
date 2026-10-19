# S4O-6 point 1 (runs ON the instance via "ssh bash -s"; read-only; no host, port or licence content): CPU, cgroup quota, disk, environment,
# the existing f50c8850 package and the S4N pilot results
echo "== lscpu"
lscpu | grep -E '^(Model name|Architecture|CPU\(s\)|Thread\(s\) per core|Core\(s\) per socket|Socket\(s\)|CPU max MHz|L3 cache|NUMA node\(s\))' | cut -c1-160
lscpu | grep -o -E 'avx512f|avx2' | sort -u | tr '\n' ' '; echo
echo "== nproc: $(nproc)"
echo "== cgroup"
if [ -r /sys/fs/cgroup/cpu.max ]; then
  echo "v2 cpu.max: $(cat /sys/fs/cgroup/cpu.max)"; echo "v2 memory.max: $(cat /sys/fs/cgroup/memory.max)"; echo "v2 memory.current: $(cat /sys/fs/cgroup/memory.current)"
else
  echo "v1 cpu.cfs_quota_us / period: $(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null) / $(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null)"
  echo "v1 memory.limit_in_bytes: $(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null)"
fi
echo "== free -g"; free -g | head -2
echo "== disk"; df -h /root/autodl-tmp / 2>&1
echo "== os"; grep PRETTY_NAME /etc/os-release; uname -r; date '+%F %T %Z'
echo "== container start (PID 1)"; ps -o lstart= -p 1
echo "== loadavg (host-wide)"; cat /proc/loadavg
echo "== tools"; for t in tmux rsync setsid; do command -v $t >/dev/null 2>&1 && echo "$t ok" || echo "$t MISSING"; done; [ -x /usr/bin/time ] && /usr/bin/time -v true >/dev/null 2>&1 && echo "/usr/bin/time ok" || echo "/usr/bin/time MISSING"
echo "== env"; PY=/root/miniconda3/envs/pypsa-earth/bin/python; [ -x $PY ] && $PY -c "import sys, pypsa, linopy, numpy, gurobipy; print('python', sys.version.split()[0], 'pypsa', pypsa.__version__, 'linopy', linopy.__version__, 'numpy', numpy.__version__, 'gurobipy', '.'.join(map(str, gurobipy.gurobi.version())))" 2>&1 | grep -v PROJ || echo "pypsa-earth env MISSING"
echo "== /root/.gurobi (names only)"; ls -la /root/.gurobi 2>/dev/null | awk 'NR>1 {print $1, $3, $5, $NF}' || echo "none"
echo "== /root/autodl-tmp"; ls /root/autodl-tmp 2>/dev/null | head -20
P=/root/autodl-tmp/s4m_cloud
if [ -d $P ]; then
  echo "== package: COMMIT $(cat $P/COMMIT 2>/dev/null); repo marker: $(cat $P/repo/.package_commit 2>/dev/null || echo none)"
  ( cd $P && echo "SHA256SUMS (f50c8850 list): $(sha256sum -c SHA256SUMS 2>&1 | awk '{print $NF}' | sort | uniq -c | tr '\n' ' ')" )
  ls $P | tr '\n' ' '; echo; ls $P/runs 2>/dev/null; ls $P/probe 2>/dev/null
else echo "== package folder $P MISSING"; fi
R=$P/runs/20261019T072454Z_5125
if [ -d $R ]; then
  echo "== pilot run folder"; ls $R | tr '\n' ' '; echo
  for f in COUNTRY_COST_LEDGER.csv SOLVE_RECEIPT.json; do [ -f $R/integrated/$f ] && echo "integrated/$f present" || echo "integrated/$f MISSING"; done
  ( cd $R && sha256sum -c results_20261019T072454Z_5125.tar.gz.sha256 2>&1 | tail -1; ls -l results_20261019T072454Z_5125.tar.gz | awk '{print $5, $NF}' )
  tail -2 $R/STATUS.txt | cut -c1-120
else echo "== pilot run folder MISSING"; fi
for f in /root/autodl-tmp/s4n_tools/PILOT_PRECISION.json; do [ -f $f ] && echo "$f present ($(stat -c %s $f) B, sha256 $(sha256sum $f | cut -c1-16))" || echo "$f MISSING"; done
echo "== running python / gurobi / tmux"; ps -eo cmd | grep -E '[p]ython|[g]urobi' | cut -c1-120; tmux ls 2>&1 | head -3
