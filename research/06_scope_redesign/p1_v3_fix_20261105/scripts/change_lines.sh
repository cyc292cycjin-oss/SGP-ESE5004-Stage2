#!/bin/bash
# Changed line ranges of the fix commits (for the report). Read-only.
set -u
cd /home/jin/wt_v3_fix
for c in ae849e1e 64aea2e3; do
  echo "=== $c $(git log -1 --format=%s $c | cut -c1-90)"
  git diff --unified=0 $c~1 $c -- . | grep -E '^(\+\+\+ b/|@@)' | sed -E 's/^\+\+\+ b\//FILE /; s/^@@ -[0-9,]+ \+([0-9]+)(,([0-9]+))? @@.*/  +\1 (\3)/'
done
echo "=== function anchors at HEAD"
grep -n -E '^def (bunker_account_premises|validate_bunker_account|bunker_metering_links|install_bunker_net_zero|blank_bunker_account_price|_efficiency_col)|^BUNKER_PRICE_NOTE' scripts_project/s4c_layers.py
grep -n -E 'research_bunker_co2_limit' scripts_project/m12_rhs_audit.py scripts_project/s4o_c1_precision.py scripts_project/l23_violation_analysis.py scripts_project/s4b_acceptance.py
grep -n -E 'blank_bunker_account_price' scripts_project/s4d_ledger.py scripts_project/v5/v5_gates.py
grep -n -E '^RUN_DIRS|RUNDIRS' scripts_project/b4_batch4.py
