#!/bin/bash
# X20 单项提交的定向测试。用法：35c_item_tests.sh <标签> <测试文件名（不含路径，可用通配）...>
cd /home/jin/wt_v5_x20
TAG=$1; shift
L=""; for p in "$@"; do L="$L $(ls tests/research/$p)"; done
bash /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/scripts/35_targeted_tests.sh "$TAG" tests/research/test_v5_x20.py tests/research/test_dfx_demand.py $L
