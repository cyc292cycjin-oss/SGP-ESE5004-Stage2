#!/bin/bash
cd /home/jin/wt_v31_review || exit 1
echo "=== runner scripts in repo ==="; git ls-files | grep -E "hpr_(job|submit|status|consistency)|make_hpc_package_v31|fullsize_presolve|zero_slack_check|BATCH_DEF_2920x3h_v31hpc" 
echo "=== python env ==="
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
$PY -c "import pypsa, linopy, xarray, pandas, numpy; print('pypsa', pypsa.__version__, 'linopy', linopy.__version__, 'xr', xarray.__version__)"
echo "=== make_hpc_package_v31.sh zero slack gate ==="
grep -n -i -E "zero_slack|ZERO_SLACK" $(git ls-files | grep make_hpc_package_v31.sh)
echo "=== ledger bunker settlement price source ==="
grep -n -E "bunker_co2|marginal_price|co2 bunkers|def country_cost_ledger|def _settle|settle" scripts_project/s4d_ledger.py | head -40
echo "=== REFERENCE_VALUES consumers ==="
git grep -n "REFERENCE_VALUES" -- scripts_project hpc_package_src hpc_v31 research/06_scope_redesign/p1_v3_20261102/hpc_v31 2>/dev/null | head -20
echo "=== b4_batch4 / gates_v6 reading price csv? ==="
git grep -n -E "NODAL_PRICES|nodal_prices_summary|note" -- scripts_project/b4_batch4.py scripts_project/v5/gates_v6.py scripts_project/s4o_c1_precision.py scripts_project/m12_allocation.py scripts_project/m12_rhs_audit.py | head
