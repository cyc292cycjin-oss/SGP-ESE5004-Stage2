#!/bin/bash
# X20 框架提交的定向测试：test_v5_x20、test_dfx_demand、test_d1_registry、全部 test_v4_*、test_m08a_a*
cd /home/jin/wt_v5_x20
bash /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/scripts/35_targeted_tests.sh "${1:-fw1}" tests/research/test_v5_x20.py tests/research/test_dfx_demand.py tests/research/test_d1_registry.py tests/research/test_v4_*.py tests/research/test_m08a_a*.py
