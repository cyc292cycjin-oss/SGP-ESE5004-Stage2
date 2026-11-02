#!/bin/bash
cd /home/jin/wt_v3_20261102
grep -n "def gate_b6_cost" -A3 scripts_project/v5/v5_gates.py | cut -c200-700
echo ==== reg
grep -rn "b6\|B6" research_inputs/registry_v5/fragments/*.csv | cut -c1-420 | head -12
echo ==== S1 / S2 reports mention
git grep -nE "第 ?48 ?项|决策 ?48|decision 48" -- 'research/06_scope_redesign/*.md' | cut -c1-320 | head -14
echo ==== item list in module spec
git grep -nE "^\| ?48 ?\|" -- 'research/*.md' | cut -c1-400 | head
