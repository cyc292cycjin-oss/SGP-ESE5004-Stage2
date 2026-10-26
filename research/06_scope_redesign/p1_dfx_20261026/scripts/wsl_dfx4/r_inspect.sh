# DFX phase 4 (runs ON the instance, read-only): identity, resources, existing files (names / sizes only), licence presence (stat only), processes,
# tools, existing environment key packages. Nothing is created, moved or changed.
echo "== identity: $(hostname) | $(TZ=Asia/Singapore date '+%F %T') SGT | uptime: $(uptime -p)"
echo "== cpu: nproc=$(nproc) nproc_all=$(nproc --all) model=$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
for f in /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.current; do [ -r $f ] && echo "cgroup $(basename $f): $(cat $f)"; done
awk '$1=="anon"||$1=="file" {printf "memory.stat %s %.2f GiB\n", $1, $2/1073741824}' /sys/fs/cgroup/memory.stat 2>/dev/null
echo "MemTotal: $(awk '/MemTotal/ {printf "%.1f GiB", $2/1048576}' /proc/meminfo)"
echo "== disks"; df -h / /root/autodl-tmp /root/autodl-fs 2>/dev/null
echo "== /root/autodl-tmp (top level)"; ls -la /root/autodl-tmp 2>&1 | head -40
echo "== sizes"; du -sh /root/autodl-tmp/* 2>/dev/null | head -30
echo "== /root/autodl-fs (top level)"; ls -la /root/autodl-fs 2>&1 | head -20
echo "== dfx dirs present?"; ls -d /root/autodl-tmp/dfx* 2>/dev/null || echo "none"
echo "== /root/.gurobi (names / stat only)"; [ -d /root/.gurobi ] && ls -la /root/.gurobi || echo "no /root/.gurobi directory"
echo "== processes (solver / runner / python)"; ps -eo pid,etimes,args | grep -E '[s]2_solve|[r]un_batch|[r]un_dfx|[g]urobi|[p]ython' | cut -c1-150 | head -20; echo "(end processes)"
echo "== tmux"; tmux ls 2>&1 | head -5
echo "== tools"; for t in /usr/bin/time setsid tmux pgrep timeout curl rsync sha256sum conda; do printf '%s: %s\n' "$t" "$(command -v $t || echo MISSING)"; done
/usr/bin/time -v true >/dev/null 2>&1 && echo "GNU time -v works" || echo "GNU time -v NOT working"
echo "== conda"; ls -d /root/miniconda3 /root/miniforge3 2>/dev/null; /root/miniconda3/bin/conda --version 2>/dev/null
echo "== existing environments"; ls -d /root/autodl-tmp/envs/* 2>/dev/null
E=/root/autodl-tmp/envs/pypsa-earth/bin/python
if [ -x $E ]; then echo "python: $($E --version 2>&1)"; $E -m pip list --format=freeze 2>/dev/null | grep -iE '^(pypsa|linopy|xarray|pandas|numpy|scipy|gurobipy|netcdf4|h5netcdf|dask|pyomo|highspy)==' ; echo "pip packages: $($E -m pip list --format=freeze 2>/dev/null | wc -l)"; fi
echo "== login-shell thread variables"; grep -hE 'OMP_NUM_THREADS|MKL_NUM_THREADS' /etc/profile.d/*.sh 2>/dev/null | head -4
echo "== nvidia"; nvidia-smi -L 2>&1 | head -2
