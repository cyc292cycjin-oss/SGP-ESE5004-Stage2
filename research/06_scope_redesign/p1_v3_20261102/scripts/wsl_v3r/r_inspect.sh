# V3 screening rerun (supplement 07) (runs ON the instance, read-only; instruction section 2 step 1): identity, resources, existing files (names / sizes only), licence
# presence (stat only), processes, tools, existing environment. Nothing is created, moved or changed.
echo "== identity: $(hostname) | $(TZ=Asia/Singapore date '+%F %T') SGT | uptime: $(uptime -p)"
echo "== cpu: nproc=$(nproc) nproc_all=$(nproc --all) model=$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
for f in /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.current; do [ -r $f ] && echo "cgroup $(basename $f): $(cat $f)"; done
for f in /sys/fs/cgroup/cpu/cpu.cfs_quota_us /sys/fs/cgroup/cpu/cpu.cfs_period_us /sys/fs/cgroup/memory/memory.limit_in_bytes; do [ -r $f ] && echo "cgroup v1 $(basename $f): $(cat $f)"; done
awk '$1=="anon"||$1=="file" {printf "memory.stat %s %.2f GiB\n", $1, $2/1073741824}' /sys/fs/cgroup/memory.stat 2>/dev/null
echo "MemTotal: $(awk '/MemTotal/ {printf "%.1f GiB", $2/1048576}' /proc/meminfo)"
echo "== disks"; df -h / /root/autodl-tmp /root/autodl-fs 2>/dev/null
echo "free data disk: $(df -Pk /root/autodl-tmp | awk 'NR==2 {printf "%d GB (decimal), %.0f GiB", $4*1024/1e9, $4/1048576}')"
echo "== /root/autodl-tmp (top level)"; ls -la /root/autodl-tmp 2>&1 | head -30
echo "== sizes"; du -sh /root/autodl-tmp/* 2>/dev/null | head -20
echo "== v3_screen present?"; ls -d /root/autodl-tmp/v3_screen_dmax 2>/dev/null || echo "none"
echo "== /root/.gurobi (names / stat only)"; [ -d /root/.gurobi ] && ls -la /root/.gurobi || echo "no /root/.gurobi directory"
echo "== processes (solver / runner / python)"; ps -eo pid,etimes,args | grep -E '[s]2_solve|[r]un_batch|[r]un_dfx|[g]urobi|[p]ython' | cut -c1-150 | head -20; echo "(end processes)"
echo "== tmux"; tmux ls 2>&1 | head -5
echo "== tools"; for t in /usr/bin/time setsid tmux pgrep timeout curl rsync sha256sum conda; do printf '%s: %s\n' "$t" "$(command -v $t || echo MISSING)"; done
/usr/bin/time -v true >/dev/null 2>&1 && echo "GNU time -v works" || echo "GNU time -v NOT working"
echo "== conda"; ls -d /root/miniconda3 /root/miniforge3 2>/dev/null; /root/miniconda3/bin/conda --version 2>/dev/null
echo "== existing environments"; ls -d /root/autodl-tmp/envs/* 2>/dev/null || echo "none on the data disk"
echo "== login-shell thread variables"; grep -hE 'OMP_NUM_THREADS|MKL_NUM_THREADS' /etc/profile.d/*.sh 2>/dev/null | head -4
echo "== locale: LANG=${LANG:-} LC_ALL=${LC_ALL:-}"
echo "== nvidia"; nvidia-smi -L 2>&1 | head -2
