#!/bin/bash
# Registered LP sizes / BUILD_CHECK / problem SHA comparisons in the package sources. Read-only.
set -u
cd /home/jin/wt_v3_fix
S="research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4 research/06_scope_redesign/p1_hpr_20261027/hpc_package_src research/06_scope_redesign/p1_v3_20261102/batch_def research/06_scope_redesign/p1_v3_20261102/hpc_v3 scripts_project/b4_batch4.py scripts_project/batch_def.py scripts_project/b4_split_solve.py"
grep -rn -E 'BUILD_CHECK|num_row|lp_rows|expected_lp|problem_sha|729156|1603380|3715722|lp_expected|LP_EXPECTED' $S | cut -c1-250 | head -50
