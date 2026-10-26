#!/bin/bash
# DFX v3 phase 3 P6 wrapper: the patterns are given here at run time only (never inside leak_scan.py); output = counts and file names, never content.
set -u
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; O=$MAIN/results_project/dfx_v3/leak_scan; mkdir -p $O
export LEAK_PATTERNS='WLSACCESSID|WLSSECRET|LICENSEID|ssh +-p +[0-9]+|(^|[^0-9.])([0-9]{1,3}\.){3}[0-9]{1,3}([^0-9.]|$)|autodl\.com|seetacloud|region-[0-9]+\.'
export LEAK_EXCLUDE='DFX_CLAUDE_CODE_INSTRUCTION\.md$'
/home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/dfx3/leak_scan.py $O/P6_LEAK_SCAN.json \
  /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_package_dfx \
  /home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026 \
  /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026
