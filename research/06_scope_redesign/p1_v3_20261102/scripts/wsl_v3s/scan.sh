#!/bin/bash
# V3 screening leak scan (before commit / push, and once more after the push). Patterns: the pattern file outside the repository (/home/jin/.dfx_leak_patterns:
# key names, ssh, ip, host) PLUS the connection values supplied only through the environment at run time (V3S_HOST, V3S_PORT) PLUS the instance name, read
# from the instance into a shell variable here (never printed, never written). Output: counts and file names only.
#   wsl env V3S_HOST=.. V3S_PORT=.. bash scan.sh [label]
set -u
source /home/jin/v3s/ssh.sh
PF=/home/jin/.dfx_leak_patterns; [ -r "$PF" ] || { echo "pattern file missing"; exit 2; }
INST=$(v3s_ssh hostname 2>/dev/null | tr -d '\r\n '); [ ${#INST} -gt 8 ] || { echo "instance name not read - refused"; exit 2; }
esc() { printf '%s' "$1" | sed 's/[.[\*^$()+?{|]/\\&/g'; }
EXTRA="$(esc "$V3S_HOST")|\\b$(esc "$V3S_PORT")\\b|$(esc "$INST")"
LEAK_PATTERNS="$(grep -v "^#" "$PF" | cut -d= -f2- | paste -sd "|" -)|$EXTRA"; export LEAK_PATTERNS
export LEAK_EXCLUDE="V3_CLAUDE_CODE_INSTRUCTION\\.md$"
export LEAK_WT=/home/jin/wt_v3_20261102 LEAK_BASE=0a20aefd
C=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T063207Z
O=/home/jin/v3s/records/LEAK_SCAN_${1:-pre}.json
/home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/v3s/leak_scan_v3.py $O \
  $LEAK_WT/research/06_scope_redesign/p1_v3_20261102 $C/analysis $C/light_unpacked > /dev/null 2>&1
echo "LEAK_SCAN_EXIT=$?"
/home/jin/miniforge3/envs/pypsa-earth/bin/python -I -c "
import json, sys
r = json.load(open(sys.argv[1]))
print('clean', r['clean'], 'patterns_supplied', r['patterns_supplied'], 'secret_values', r['n_secret_values'], 'commits', r['n_commits'])
for t, v in r['targets'].items():
    print(t.split('/')[-1], 'files', v['files'], 'binary', v['binary'], 'hit_files', v['n_hit_files'], [(h['file'], h['value_hits'], h['pattern_hits']) for h in v['hits']][:12], 'excluded', v['excluded'][:5])
print('commits with hits', {k: v for k, v in r['commits'].items() if v['value_hits'] or v['pattern_hits']})
" $O
