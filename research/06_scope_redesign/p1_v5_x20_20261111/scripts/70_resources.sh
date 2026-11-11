#!/bin/bash
# B 段结束记录：WSL df -h /、D 盘 df、交付目录大小（含与不含网络）、worktree 与其 git 元数据大小、/tmp 残留、WSL 内存
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
date -u +%FT%TZ
df -h / | tail -1; df -h /mnt/d | tail -1
du -sb $D | cut -f1 | sed 's/^/delivery_bytes /'
for s in builds trunc56 smoke56 cache downloads logs evidence scripts tmp tmp_solve pycache pytest_tmp v4work x20_src profiles; do [ -e $D/$s ] && echo "$s $(du -sb $D/$s | cut -f1)"; done
du -sb /home/jin/wt_v5_x20 | cut -f1 | sed 's/^/worktree_bytes /'
du -sb /home/jin/wt_v5_x20/.git 2>/dev/null | cut -f1 | sed 's/^/worktree_gitfile /'
G=$(git -C /home/jin/wt_v5_x20 rev-parse --git-dir); du -sb $G | cut -f1 | sed "s#^#worktree_gitdir_bytes #"
find /home/jin/wt_v5_x20 -name __pycache__ -type d -prune -exec du -sb {} + | awk '{s+=$1} END {print "pycache_bytes", s}'
ls -d /tmp/x20_* 2>/dev/null | head; du -sb /tmp 2>/dev/null | cut -f1 | sed 's/^/tmp_bytes /'
awk '/MemAvailable|MemTotal/{printf "%s %d MiB\n", $1, $2/1024}' /proc/meminfo
