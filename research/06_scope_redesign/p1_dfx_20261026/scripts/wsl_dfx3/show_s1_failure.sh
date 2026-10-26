#!/bin/bash
f=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/tests/full.log
awk 'index($0, "_ BuiltNetworks.test_static_validation_passes_on_reload _") {p=1} p {print} /^=+ (short test summary|warnings summary)/ {p=0}' "$f" | grep -v -E "Warning|warn\(" | sed -n '60,140p'
echo "=== test_s1_built_networks.py head"; sed -n 1,22p /home/jin/wt_dfx_v3_20261026/tests/research/test_s1_built_networks.py | cut -c1-220
echo "=== B4P / M10 reports on this test"; grep -n -i -E "test_s1_built_networks|2 failed|failed, " /mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026/B4P_REPORT.md /mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10_20261022/M10_REPORT.md /mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026/B4P_PROGRESS.md 2>/dev/null | cut -c1-300 | head -12
