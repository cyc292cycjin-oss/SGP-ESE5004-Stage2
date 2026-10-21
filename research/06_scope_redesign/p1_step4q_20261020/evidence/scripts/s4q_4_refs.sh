#!/bin/bash
W=/home/jin/wt_s4q_20261020/research/06_scope_redesign
grep -rh "Barrier solved model\|Barrier performed\|^Optimal objective\|Sub-optimal" $W/p1_step4n_20261019/cloud_results/*/unpacked/*/export_integrated/GUROBI_LOG_SCRUBBED.txt 2>/dev/null | head -5
ls $W/p1_step4n_20261019/cloud_results/*/unpacked/*/ 2>/dev/null | head -30
grep -rl "Barrier solved model" $W/p1_step4n_20261019 2>/dev/null | head -5
echo == s4o6; ls $W/p1_step4o_20261019/evidence/s4o_6/ | head -30
grep -rh "Barrier performed\|Barrier solved" $W/p1_step4o_20261019/evidence/s4o_6 2>/dev/null | head -6
