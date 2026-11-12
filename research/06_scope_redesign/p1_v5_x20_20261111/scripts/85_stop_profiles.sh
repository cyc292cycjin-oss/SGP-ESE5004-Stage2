#!/bin/bash
# 暂停用：列出并终止本任务启动的 s4a_profiles.py 进程（只匹配该脚本名；不碰其他进程）
P=$(pgrep -f "[s]4a_profiles.py --variant calibrated_modern calibrated_gwa_v5 calibrated_gwa_v5q")
echo "running: ${P:-none}"
[ -n "$P" ] && { kill $P; sleep 2; echo "after kill: $(pgrep -f '[s]4a_profiles.py' || echo none)"; }
ls -la /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/profiles/onwind_q_c1 2>/dev/null | head
