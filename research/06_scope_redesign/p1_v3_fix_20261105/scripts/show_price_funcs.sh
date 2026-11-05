#!/bin/bash
# Print the price / emission report functions. Read-only.
set -u
cd /home/jin/wt_v3_fix
echo "== s4d_ledger.nodal_prices"; sed -n '303,330p' scripts_project/s4d_ledger.py
echo "== v5_gates.nodal_prices"; sed -n '/^def nodal_prices/,/^def /p' scripts_project/v5/v5_gates.py | head -40
echo "== emission_report"; git grep -n 'def emission_report' -- scripts_project
f=$(git grep -l 'def emission_report' -- scripts_project | head -1); sed -n '/^def emission_report/,/^def /p' "$f" | head -50
echo "== consumers of NODAL_PRICES.csv / nodal_prices_summary.csv"
git grep -n -E 'NODAL_PRICES\.csv|nodal_prices_summary' -- scripts_project '*.sh' ':!research/' | cut -c1-200
echo "== s4d_ledger owners / bus_entities"; sed -n '44,102p' scripts_project/s4d_ledger.py
