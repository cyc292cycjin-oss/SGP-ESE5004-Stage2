#!/bin/bash
cd /home/jin/wt_v3_20261102
for k in 10 15 17 18 20 35 36 41 43 44 48 59 64 88 89 91 92 93 95 96 119 132; do
  echo "=== $k"
  git grep -hE "^\| ?$k ?\|" -- 'research/06_scope_redesign/*INSTRUCTION*.md' 'research/06_scope_redesign/*REPORT*.md' | cut -c1-520 | sort -u | head -3
done
echo "=== gate_b6_cost callers"
grep -n "gate_b6_cost\|existing_cross_border_fom_eur" scripts_project/s2_solve.py scripts_project/v5/*.py scripts_project/m10_batch3_summary.py scripts_project/m12_allocation.py scripts_project/s4o_c1_precision.py | cut -c1-240
