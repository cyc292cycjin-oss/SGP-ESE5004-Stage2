#!/bin/bash
# DFX phase 4 leak scan (before commit / push). Patterns: the pattern file outside the repository (/home/jin/.dfx_leak_patterns: key names, ssh,
# ip, host) PLUS the connection values of this session supplied only through the environment at run time (DFX_HOST, DFX_PORT, DFX_INST = the
# instance name); nothing of them is written in this file. Output: counts and file names only (leak_scan.py never prints matched text).
#   wsl env DFX_HOST=.. DFX_PORT=.. DFX_INST=.. bash p4_scan.sh
set -u
: "${DFX_HOST:?}" "${DFX_PORT:?}" "${DFX_INST:?}"
PF=/home/jin/.dfx_leak_patterns; [ -r "$PF" ] || { echo "pattern file missing"; exit 2; }
esc() { printf '%s' "$1" | sed 's/[.[\*^$()+?{|]/\\&/g'; }
EXTRA="$(esc "$DFX_HOST")|\\b$(esc "$DFX_PORT")\\b|\\b$(esc "$DFX_INST")\\b"
LEAK_PATTERNS="$(grep -v "^#" "$PF" | cut -d= -f2- | paste -sd "|" -)|$EXTRA"; export LEAK_PATTERNS
export LEAK_EXCLUDE="DFX_CLAUDE_CODE_INSTRUCTION\\.md$"
O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/leak_scan; mkdir -p $O
D=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026
/home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/dfx3/leak_scan.py $O/P4_LEAK_SCAN.json \
  $D \
  /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_results/final_20261026T223024Z/analysis \
  /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_results/final_20261026T223024Z/light_unpacked > /dev/null 2>&1
rc=$?; echo "LEAK_SCAN_EXIT=$rc"
/home/jin/miniforge3/envs/pypsa-earth/bin/python -I -c "
import json, sys
r = json.load(open(sys.argv[1]))
print('patterns_supplied', r['patterns_supplied'], 'secret_values', r['n_secret_values'])
for t, v in r['targets'].items():
    print(t.split('/')[-1], 'files', v['files'], 'hit_files', v['n_hit_files'], [h['file'] for h in v['hits']][:10])
c = r.get('commits') or {}
print('commits scanned', len(c), 'commits with hits', [k[:8] for k, v in c.items() if (v.get('value_hits') or v.get('pattern_hits'))])
" $O/P4_LEAK_SCAN.json
