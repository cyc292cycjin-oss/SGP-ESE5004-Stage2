#!/bin/bash
# Producers of EMISSIONS_BY_COUNTRY / price outputs and marginal_price readers in the post-solve chain. Read-only.
set -u
cd /home/jin/wt_v3_fix
echo "== producers of output files mentioning emissions / prices"
git grep -n -E 'EMISSIONS_BY_COUNTRY|PRICES?\.json|PRICE_SUMMARY|co2_price|price_by_country|nodal_prices' -- scripts_project | cut -c1-200 | head -30
echo
echo "== marginal_price readers in scripts_project (non-test, non-retired)"
git grep -n -l 'marginal_price' -- scripts_project ':!scripts_project/retired' | sort
echo
echo "== s4d_ledger.py marginal_price lines"
grep -n -E 'marginal_price|def ' scripts_project/s4d_ledger.py | cut -c1-200
