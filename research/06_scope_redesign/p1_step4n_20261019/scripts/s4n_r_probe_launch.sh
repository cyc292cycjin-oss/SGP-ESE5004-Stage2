#!/bin/bash
# S4N-3 speed probe launcher (runs ON the instance inside tmux session s4n_probe). No host, port or licence content here.
cd /root/autodl-tmp/s4m_cloud
T=$(TZ=Asia/Singapore date "+%Y-%m-%d %H:%M")
AUTH="用户授权（2026-10-19 S4N 启动消息）：在 AutoDL 西北 B 区 D58 机（克隆自 L23 实例；Intel Xeon Platinum 8470Q，容器配额 25 核 / 120 GiB，数据盘 50 GB）上运行 S4M 部署包（代码 f50c8850）的速度探针：一次 56×3h 一体化求解，求解档案 A（formal_barrier），30 分钟止损，不重试、不改参数、不 warm start；r ≥ 0.5 才继续试点。许可文件 /root/.gurobi/gurobi.lic，只经 GRB_LICENSE_FILE 引用，结果回收后删除。时间：${T}（SGT）。"
echo "PROBE_LAUNCH:${T} SGT" > /root/autodl-tmp/s4n_probe_launch.txt
echo "AUTH:${AUTH}" >> /root/autodl-tmp/s4n_probe_launch.txt
PY=/root/miniconda3/envs/pypsa-earth/bin/python GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic bash speed_probe.sh --auth "$AUTH" > /root/autodl-tmp/s4n_probe_console.log 2>&1
echo "PROBE_EXIT:$? $(TZ=Asia/Singapore date '+%F %T') SGT" >> /root/autodl-tmp/s4n_probe_launch.txt
