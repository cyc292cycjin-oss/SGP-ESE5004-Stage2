#!/bin/bash
f=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/tests/full.log
for t in test_parallel_when_the_probe_passes test_f0_changed_scripts_in_the_executed_lists test_static_validation_passes_on_reload; do
  echo "=================== $t"
  awk -v t="$t" 'index($0, "_ " t " _") {p=1} p {print} /^(FAILED|=+ short test summary|_{5,} test_)/ && p && !index($0, t) {p=0}' "$f" | grep -v -E "Warning|warn\(" | head -60
done
echo "=== test_f0 source"; grep -n -A28 "^def test_f0_changed_scripts_in_the_executed_lists" /home/jin/wt_dfx_v3_20261026/tests/research/test_dfx_demand.py | head -45
