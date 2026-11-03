#!/bin/bash
cd /home/jin/wt_v3_hpc || exit 1
ls research/06_scope_redesign/p1_hpr_20261027/ research/06_scope_redesign/p1_hpr_20261027/hpc_package_src research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/* research/06_scope_redesign/p1_hpr_20261027/scripts 2>&1 | head -80
echo ---
ls research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/ 2>&1
echo ---
ls research/06_scope_redesign/p1_v3_20261102/batch_def research/06_scope_redesign/p1_v3_20261102/screen_package research/06_scope_redesign/p1_v3_20261102/scripts
echo ---
wc -l scripts_project/b4_batch4.py scripts_project/batch_def.py scripts_project/b4_split_solve.py scripts_project/s2_solve.py
git log --oneline 0a20aefd -3
git log --oneline 0a20aefd..5e372e5d | wc -l
