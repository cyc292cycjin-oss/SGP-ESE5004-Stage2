#!/bin/bash
# X20 §3 第 4 步 (c)：s3_6_gates_check.py（B1 范围、B11-B16）于 v5 主集 F1 / F2 2920x3h；构建回执 SHA 对照。门控同 68_run.sh（两张网络约 1.6 GiB）。
set -u
MAIN=${X20_MAIN:-v5main}; TAG=${X20_TAG:-}; export X20_MAIN=$MAIN X20_OFF=${X20_OFF:-v5off} X20_TAG=$TAG
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
AV=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo); echo "MemAvailable_MiB $AV"; [ "$AV" -ge 4096 ] || { echo "GATE REFUSED"; exit 3; }
cd $R || exit 1
env -u GRB_LICENSE_FILE /usr/bin/time -v $PY scripts_project/s3_6_gates_check.py --repo . --integrated $D/builds/$MAIN/integrated/integrated_2920_3h_unsolved.nc \
  --disconnected $D/builds/$MAIN/no_new_xb/no_new_xb_2920_3h_unsolved.nc --output $D/evidence/S3_6_GATES_V5$TAG.json > $D/logs/68b_s36$TAG.txt 2> $D/logs/68b_s36$TAG.err
echo "S36_EXIT:$?"; grep -v -iE 'warn|INFO:|PROJ' $D/logs/68b_s36$TAG.txt | tail -20 | cut -c1-400; grep -E 'Maximum resident|Elapsed' $D/logs/68b_s36$TAG.err; grep -E "Traceback|Error" $D/logs/68b_s36$TAG.err | tail -3
$PY $D/scripts/68b_receipts.py
