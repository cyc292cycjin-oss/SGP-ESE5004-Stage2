#!/bin/bash
# S4N-4 pilot launcher (runs ON the instance inside tmux session s4n): ONE integrated STEPS 365x24h run, profile A, serial, TimeLimit / wall cap
# from the speed probe (environment GUROBI_TIME_LIMIT_S / WALL_CAP_S given in the tmux command). No host, port or licence content here.
: "${GUROBI_TIME_LIMIT_S:?}" "${WALL_CAP_S:?}"
cd /root/autodl-tmp/s4m_cloud
T=$(TZ=Asia/Singapore date "+%Y-%m-%d %H:%M")
AUTH="用户授权（2026-10-19 S4N 启动消息）：在 AutoDL 西北 B 区 D58 机（克隆自 L23 实例；Intel Xeon Platinum 8470Q，容器配额 25 核 / 120 GiB，数据盘 50 GB）上运行 S4M 部署包（代码 f50c8850）的 365×24h 一体化 STEPS 试点（一次，--runs integrated），求解档案 A（formal_barrier），运行方式 serial，每运行 TimeLimit ${GUROBI_TIME_LIMIT_S} s、墙钟上限 ${WALL_CAP_S} s（按速度探针建议），不重试、不改参数、不 warm start；整批运行未授权。许可文件 /root/.gurobi/gurobi.lic，只经 GRB_LICENSE_FILE 引用，结果回收后删除。时间：${T}（SGT）。"
echo "PILOT_LAUNCH:${T} SGT time_limit_s:${GUROBI_TIME_LIMIT_S} wall_cap_s:${WALL_CAP_S}" > /root/autodl-tmp/s4n_pilot_launch.txt
echo "AUTH:${AUTH}" >> /root/autodl-tmp/s4n_pilot_launch.txt
PY=/root/miniconda3/envs/pypsa-earth/bin/python GRB_LICENSE_FILE=/root/.gurobi/gurobi.lic GUROBI_TIME_LIMIT_S=$GUROBI_TIME_LIMIT_S WALL_CAP_S=$WALL_CAP_S \
  bash run_365x24h.sh --solver-profile formal_barrier --mode serial --runs integrated --auth "$AUTH" > /root/autodl-tmp/s4n_pilot_console.log 2>&1
echo "RUN_SCRIPT_EXIT:$? $(TZ=Asia/Singapore date '+%F %T') SGT" >> /root/autodl-tmp/s4n_pilot_launch.txt
