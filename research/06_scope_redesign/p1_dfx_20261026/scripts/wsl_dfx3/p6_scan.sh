#!/bin/bash
# DFX v3 phase 3 P6 wrapper: the search patterns are NOT written in any repository file - they are read at run time from a pattern file OUTSIDE the
# repository, the package and the work folder (/home/jin/.dfx_leak_patterns, lines name=regex: key, ssh, ip, host). Output = counts and file names only.
set -u
PF=${LEAK_PATTERN_FILE:-/home/jin/.dfx_leak_patterns}; [ -r "$PF" ] || { echo "pattern file $PF missing (write it outside the repository; never commit it)"; exit 2; }
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; O=$MAIN/results_project/dfx_v3/leak_scan; mkdir -p $O
LEAK_PATTERNS=$(grep -v "^#" "$PF" | cut -d= -f2- | paste -sd "|" -); export LEAK_PATTERNS
export LEAK_EXCLUDE="DFX_CLAUDE_CODE_INSTRUCTION\\.md$"
/home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/dfx3/leak_scan.py $O/P6_LEAK_SCAN.json \
  /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_package_dfx \
  /home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026 \
  /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026
