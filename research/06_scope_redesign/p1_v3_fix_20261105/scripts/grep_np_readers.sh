#!/bin/bash
# How are NODAL_PRICES.csv / marginal_price read? Read-only.
set -u
cd /home/jin/wt_v3_fix
echo "== l23_c9_summary 175-195"; sed -n '175,195p' scripts_project/l23_c9_summary.py
echo "== s4l_2_summary 95-125, 185-200"; sed -n '95,125p;185,200p' scripts_project/s4l_2_summary.py
echo "== m12_allocation marginal_price"; grep -n 'marginal_price' scripts_project/m12_allocation.py | cut -c1-220
echo "== v3_smoke_eval marginal_price / bunker"; grep -n -E 'marginal_price|bunker|BUNKER' scripts_project/v3_smoke_eval.py | cut -c1-220
echo "== b4_batch4 / gates_v6 / pack_results reading NODAL"; grep -rn -E 'NODAL_PRICES|nodal_prices_summary' scripts_project/b4_batch4.py scripts_project/v5/gates_v6.py research/06_scope_redesign/p1_m10p_20261022/cloud_package/pack_results.sh research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh | cut -c1-200
