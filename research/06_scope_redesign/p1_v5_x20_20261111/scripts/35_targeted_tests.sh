#!/bin/bash
# X20：定向测试（不求解）。用法：35_targeted_tests.sh <标签> <pytest 参数...>；日志 logs/ut_<标签>.txt
set -u
TAG=${1:?tag}; shift
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; LOG=$D/logs/ut_$TAG.txt
cd $R || exit 1
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
export V4_D2A_BUILD=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w14/builds/main/integrated/integrated_365_24h_unsolved.nc
BT=/tmp/x20_pytest_$TAG; rm -rf "$BT"
echo "HEAD $(git rev-parse HEAD); dirty files $(git status --short | wc -l)" > $LOG
$PY -m py_compile $(git status --short | awk '{print $2}' | grep '\.py$') >> $LOG 2>&1 && echo "py_compile OK" >> $LOG
start=$(date +%s)
$PY -m pytest -q -p no:cacheprovider --basetemp=$BT "$@" -rfEs >> $LOG 2>&1; rc=$?
echo "EXIT:$rc seconds:$(( $(date +%s) - start ))" >> $LOG; rm -rf "$BT"
tail -15 $LOG
