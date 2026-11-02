#!/bin/bash
cd /home/jin/wt_v3_20261102/scripts_project
sed -n 559,568p s2_solve.py | tr ';' '\n' | grep -oE 'add_argument\("--[a-z-]+"[^)]{0,60}' | cut -c14-90
grep -n "stop_before_solve" s2_solve.py | cut -c1-190 | head -8
grep -n "s2_solve.py\|stop-before" /home/jin/wt_v3_20261102/research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh 2>/dev/null | cut -c1-220 | head -6
