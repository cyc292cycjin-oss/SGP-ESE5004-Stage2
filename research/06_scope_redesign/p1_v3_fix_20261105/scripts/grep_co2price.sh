#!/bin/bash
# Outputs that may report the bunker account price (marginal price of 'co2 bunkers ASEAN' = the old scalar dual through the Store chain). Read-only.
set -u
cd /home/jin/wt_v3_fix
FILES="scripts_project/s2_solve.py scripts_project/s4d_ledger.py scripts_project/s4d_ledger_redo.py scripts_project/m12_allocation.py scripts_project/m12_rhs_audit.py scripts_project/b4_batch4.py scripts_project/s4o_c1_precision.py scripts_project/l23_violation_analysis.py scripts_project/v5/gates_v6.py scripts_project/v5/v5_gates.py scripts_project/s4b_acceptance.py scripts_project/s4c_layers.py scripts_project/s1_solve.py"
grep -n -i -E 'co2[ _]?price|carbon[ _]?price|shadow|marginal_price.*co2|co2.*marginal_price|atmosphere.*marginal|mu_|BUNKER_CO2_BUS|bunkers ASEAN' $FILES | cut -c1-230
echo "== which modules does s2_solve import for post-solve exports"
grep -n -E '^\s*from [a-z0-9_]+ import|^\s*import [a-z0-9_]+' scripts_project/s2_solve.py | sort -u -t: -k3 | cut -c1-160 | head -60
