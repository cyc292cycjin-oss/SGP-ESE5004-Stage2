#!/bin/bash
# M12b：合并结果与 M08b 头 / ec80668f 的模型相关差异（只读）
set -u
cd /home/jin/wt_m12_20261021 || exit 1
git add research/STAGE2_PROJECT_LEDGER.md
echo "=== unmerged left: $(git diff --name-only --diff-filter=U | wc -l)"
echo "=== index vs M08b head b018670c (all paths)"
git diff --cached --stat b018670c | tail -40
echo "=== index vs ec80668f: configs / model code (excluding m12 and run-batch files)"
git diff --cached --stat ec80668f -- configs scripts_project research_inputs | grep -v "m12_\|m08a_run_batch" | tail -20
echo "=== configs diff vs ec80668f"
git diff --cached ec80668f -- configs | head -20
echo "=== m08a_variants / m08a_layers / s2_solve / gates_v6 / s4o_c1 / l23 vs b018670c"
git diff --cached --stat b018670c -- scripts_project/m08a_variants.py scripts_project/m08a_layers.py scripts_project/s2_solve.py scripts_project/v5/gates_v6.py scripts_project/s4o_c1_precision.py scripts_project/l23_violation_analysis.py
