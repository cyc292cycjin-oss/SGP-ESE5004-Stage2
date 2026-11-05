#!/bin/bash
# Hard-coded run directory names / HPC folder in the package sources. Read-only.
set -u
cd /home/jin/wt_v3_fix
S="research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/preflight.sh research/06_scope_redesign/p1_hpr_20261027/hpc_package_src research/06_scope_redesign/p1_m10p_20261022/cloud_package/pack_results.sh scripts_project/b4_batch4.py scripts_project/batch_def.py research/06_scope_redesign/p1_v3_20261102/batch_def/BATCH_DEF_2920x3h_v3hpc.json"
grep -rn -E 'batch4|smoke56|hpr3|RUN_DIR|run_dir|runs/' $S | grep -v -E '^\S+:\s*#' | cut -c1-210 | head -120
