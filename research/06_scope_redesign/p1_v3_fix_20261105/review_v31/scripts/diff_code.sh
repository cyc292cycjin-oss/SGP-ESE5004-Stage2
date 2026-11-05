#!/bin/bash
cd /home/jin/wt_v31_review || exit 1
git diff 7d22dda1 1117a07f -- scripts_project/s4c_layers.py scripts_project/m12_rhs_audit.py scripts_project/s4b_acceptance.py scripts_project/s4d_ledger.py scripts_project/s4o_c1_precision.py scripts_project/v5/v5_gates.py scripts_project/l23_violation_analysis.py scripts_project/b4_batch4.py tests/research/test_dfx_demand.py
