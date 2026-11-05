#!/bin/bash
cd /home/jin/wt_v31_review || exit 1
echo "=== b4_batch4.py projection ==="
grep -n -A40 "def projection" scripts_project/b4_batch4.py | head -70
echo "=== m12_allocation marginal_price usage ==="
grep -n -E "marginal_price|nodal_prices|NODAL_PRICES" scripts_project/m12_allocation.py scripts_project/m12_rhs_audit.py scripts_project/v5/gates_v6.py scripts_project/s4o_c1_precision.py | head -20
echo "=== s2_solve guard nodal_prices_summary and B1_BUNKERS ==="
grep -n -E "bunker_account_report|B1_BUNKERS|nodal_prices" scripts_project/s2_solve.py | head
echo "=== test_v31_bunker_fix.py heads ==="
grep -n -E "^def test_|^    def test_" tests/research/test_v31_bunker_fix.py tests/research/test_v31_hpc_package.py
