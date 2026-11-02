#!/bin/bash
cd /home/jin/wt_v3_20261102
echo "=== decision register candidates"
git ls-files research | grep -iE 'decision|决策|LEDGER|REGISTER' | head -30
ls -la research/*.md 2>/dev/null | head
echo "=== grep decision 48"
git grep -nE "(decision|决策|第|item) ?48\b" -- 'research/*.md' 'configs/*' 'research_inputs/registry_v5/fragments/*.csv' | cut -c1-260 | head -20
echo "=== v5_gates gate_b5/b6"
sed -n 95,140p scripts_project/v5/v5_gates.py | cut -c1-240
