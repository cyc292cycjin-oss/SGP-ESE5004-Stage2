#!/bin/bash
# X20 §3 第 4 步：静态核对（68_static_w14.py，含 56 时段切分）与 V3.1 零松弛门（zero_slack_check.py，4 张网络）。不求解，不用许可证。
# 门控：可用 >= 4 GiB，且估计峰值 3.5 GiB（三张 2920 网络）<= 可用的一半 -> 可用 >= 7 GiB；有求解进程时拒绝。
set -u
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
[ "$(ps -eo args= | grep -v x20_pytest | grep -cE '[s]2_solve\.py|[g]urobi_cl')" = 0 ] || { echo "REFUSED: a solve is running"; exit 2; }
AV=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo); echo "MemAvailable_MiB $AV"
[ "$AV" -ge 7168 ] || { echo "GATE REFUSED: available < 7 GiB"; exit 3; }
echo "== static $(date -u +%FT%TZ)"
cd $R || exit 1
env -u GRB_LICENSE_FILE /usr/bin/time -v $PY $D/scripts/68_static_w14.py > $D/logs/68_static.txt 2> $D/logs/68_static.err; echo "STATIC_EXIT:$?"
grep -v -iE 'warn|INFO:|PROJ' $D/logs/68_static.txt | cut -c1-600; grep -E 'Maximum resident|Elapsed' $D/logs/68_static.err; grep -iE "Traceback|Error" $D/logs/68_static.err | tail -5
AV=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo); echo "MemAvailable_MiB $AV"; [ "$AV" -ge 4096 ] || { echo "GATE REFUSED before zero slack"; exit 3; }
echo "== zero slack $(date -u +%FT%TZ)"
env -u GRB_LICENSE_FILE /usr/bin/time -v $PY scripts_project/zero_slack_check.py --repo . --out $D/evidence/ZERO_SLACK_CHECK_V5.json \
  --network v5_F1=integrated:$D/builds/v5main/integrated/integrated_2920_3h_unsolved.nc --network v5_F2=no_new_xb:$D/builds/v5main/no_new_xb/no_new_xb_2920_3h_unsolved.nc \
  --network v5_F1_56=integrated:$D/trunc56/v5main_integrated_56.nc --network v5_F2_56=no_new_xb:$D/trunc56/v5main_no_new_xb_56.nc > $D/logs/68_zero_slack.txt 2> $D/logs/68_zero_slack.err
echo "ZERO_SLACK_EXIT:$?"; grep -v -iE 'warn|INFO:|PROJ' $D/logs/68_zero_slack.txt | tail -8 | cut -c1-600; grep -E 'Maximum resident|Elapsed' $D/logs/68_zero_slack.err
echo "CHECKS_DONE $(date -u +%FT%TZ)"
