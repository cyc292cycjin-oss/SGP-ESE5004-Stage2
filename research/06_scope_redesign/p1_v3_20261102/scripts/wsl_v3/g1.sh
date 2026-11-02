#!/bin/bash
cd /home/jin/wt_v3_20261102/scripts_project
echo "=== B6 / decision 48"
grep -nE "\bB6\b|b6_|decision 48|item 48|第 48 项|existing_capex_constant|objective_constant|net_of_constants" *.py v5/*.py | grep -vE '^(s[0-9]_|s4[a-n]_[0-9]|l23_c9|s3_7|s4b_5|s4c_6|s4d_[0-9]|s4e_[0-9]|s4f_[0-9]|s4g_[0-9]|s4h_[0-9]|s4j_[0-9]|s4k_[0-9]|s4l_[0-9]|s4m_[0-9])' | cut -c1-200 | head -60
echo "=== scenario names in prod post-processing"
grep -nE "\"disconnected\"|'disconnected'|integrated" v5/gates_v6.py v5/v5_gates.py s2_solve.py s4o_c1_precision.py m12_rhs_audit.py b4_batch4.py | cut -c1-220 | head -60
echo "=== configs"
ls ../configs/research/ ; for f in ../configs/research/integrated.yaml ../configs/research/disconnected.yaml; do echo "--- $f"; cat $f; done
echo "=== phase4_static.config"
grep -n "def config" -A22 phase4_static.py | cut -c1-200
