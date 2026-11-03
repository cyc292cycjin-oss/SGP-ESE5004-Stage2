#!/bin/bash
# V3 HPC package leak scan (instruction V14 section 6.3; before the final commit / push and once more after the push). Patterns: the pattern file OUTSIDE the
# repository (/home/jin/.dfx_leak_patterns: key names, ssh, ip, host) read at run time, plus the values of the local licence file compared in memory by
# leak_scan_v3.py (never printed). No AutoDL / instance connection in this step, so no connection values. Output: counts and file names only.
#   bash scan_h.sh [label]
set -u
PF=/home/jin/.dfx_leak_patterns; [ -r "$PF" ] || { echo "pattern file missing"; exit 2; }
LEAK_PATTERNS="$(grep -v "^#" "$PF" | cut -d= -f2- | paste -sd "|" -)"; [ ${#LEAK_PATTERNS} -gt 8 ] || { echo "empty patterns - refused"; exit 2; }; export LEAK_PATTERNS
export LEAK_EXCLUDE="V3_CLAUDE_CODE_INSTRUCTION\\.md$|wsl_v3/commit_p1\\.sh$|/dry_[0-9TZ]+/|/v3h/bash42/"   # bash42/: the downloaded GNU bash 4.2 source and build (third party, never shipped or committed)
export LEAK_WT=/home/jin/wt_v3_hpc LEAK_BASE=5e372e5d
O=/home/jin/v3h/LEAK_SCAN_${1:-pre}.json
/home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/v3h/leak_scan_v3.py $O \
  $LEAK_WT/research/06_scope_redesign/p1_v3_20261102 /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3 \
  $LEAK_WT/research/06_scope_redesign/p1_hpr_20261027/hpc_package_src $LEAK_WT/research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4 /home/jin/v3h > /home/jin/v3h/leak_scan_${1:-pre}.out 2>&1
echo "LEAK_SCAN_EXIT=$?"
/home/jin/miniforge3/envs/pypsa-earth/bin/python -I -c "
import json, sys
r = json.load(open(sys.argv[1]))
print('clean', r['clean'], 'secret_values', r['n_secret_values'], 'patterns', r['patterns_supplied'], 'commits', r['n_commits'])
for t, v in r['targets'].items(): print(t.split('/')[-1], 'files', v['files'], 'hit_files', [(h['file'], h['value_hits'], h['pattern_hits']) for h in v['hits']][:12], 'excluded', len(v['excluded']))
print('commits_with_hits', {k: (v['value_hits'], v['pattern_hits'], v['files'][:6]) for k, v in r['commits'].items() if v['value_hits'] or v['pattern_hits']})
" $O
