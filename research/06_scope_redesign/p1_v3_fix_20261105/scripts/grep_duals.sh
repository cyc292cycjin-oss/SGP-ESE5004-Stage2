#!/bin/bash
# Where do the post-processing scripts read constraint duals? Read-only.
set -u
cd /home/jin/wt_v3_fix
for f in scripts_project/m12_allocation.py scripts_project/s4d_ledger.py scripts_project/s4d_ledger_redo.py scripts_project/s4o_c1_precision.py scripts_project/l23_violation_analysis.py scripts_project/b4_split_solve.py scripts_project/s4m_duals.py scripts_project/v5/gates_v6.py scripts_project/b4_batch4.py; do
  echo "=================== $f"
  grep -n -E '\.dual\b|dual_of|DUALS_BY_CONSTRAINT|constraints\[|m\.constraints|in m\.constraints|Pi\.npy|shadow|bunker|BUNKER' "$f" | cut -c1-230 | head -40
done
echo "=================== run_batch4.sh post steps"
R=research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh
grep -n -E 'l23_violation_analysis|s4o_c1_precision|m12_allocation|m12_rhs_audit|s4d_ledger_redo|gates_v6|s4m_duals|--split-stage' "$R" | cut -c1-260
