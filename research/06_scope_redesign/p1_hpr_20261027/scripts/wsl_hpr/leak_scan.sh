#!/bin/bash
# HPR H-P8 wrapper: the search patterns are NOT written in any repository file - they are read at run time from the pattern file OUTSIDE the repository
# (/home/jin/.dfx_leak_patterns, lines name=regex: key, ssh, ip, host, ...). Extra run-time patterns may be given in LEAK_EXTRA (regex). Output = counts
# and file names only (leak_scan.py never prints matched text). Targets: package v9, deliverable folder (worktree), Windows work folder, WSL helper folder.
set -u
PF=${LEAK_PATTERN_FILE:-/home/jin/.dfx_leak_patterns}; [ -r "$PF" ] || { echo "pattern file $PF missing (write it outside the repository; never commit it)"; exit 2; }
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; O=$MAIN/results_project/hpr/leak_scan; mkdir -p $O
LEAK_PATTERNS=$(grep -v "^#" "$PF" | cut -d= -f2- | paste -sd "|" -); [ -z "${LEAK_EXTRA:-}" ] || LEAK_PATTERNS="$LEAK_PATTERNS|$LEAK_EXTRA"; export LEAK_PATTERNS
export LEAK_EXCLUDE="HPR_CLAUDE_CODE_INSTRUCTION\\.md$|DFX_CLAUDE_CODE_INSTRUCTION\\.md$"
/home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/hpr/leak_scan.py $O/HPR_LEAK_SCAN.json \
  /mnt/d/ResearchWorkspaces/ASEAN/work/p1_hpr_20261027/hpc_package \
  /home/jin/wt_hpr_20261027/research/06_scope_redesign/p1_hpr_20261027 \
  /mnt/d/ResearchWorkspaces/ASEAN/work/p1_hpr_20261027 \
  /home/jin/hpr
echo "LEAK_SCAN_EXIT=$?"
