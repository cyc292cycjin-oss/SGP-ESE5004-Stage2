#!/bin/bash
# V3.1 leak scan (instruction section 6.4; before the final commit / push and once more after the push). Patterns: the pattern file OUTSIDE the repository
# (/home/jin/.dfx_leak_patterns: key names, ssh, ip, host) read at run time, plus the values of the local licence file compared in memory by leak_scan_v3.py
# (never printed). Output: counts and file names only; leak_classify.py gives masked matches for the review of every hit.
#   bash scan_fix.sh <label> [package dir]
set -u
L=${1:?label}; PKGD=${2:-/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1}
S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/scripts; EV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/evidence/leak; mkdir -p "$EV"
PF=/home/jin/.dfx_leak_patterns; [ -r "$PF" ] || { echo "pattern file missing"; exit 2; }
LEAK_PATTERNS="$(grep -v "^#" "$PF" | cut -d= -f2- | paste -sd "|" -)"; [ ${#LEAK_PATTERNS} -gt 8 ] || { echo "empty patterns - refused"; exit 2; }; export LEAK_PATTERNS
export LEAK_EXCLUDE="/dry_[0-9TZ]+/|/drill_pkg_[0-9a-f]+/runs/|/v3fix/bash42_shim/"
export LEAK_WT=/home/jin/wt_v3_fix LEAK_BASE=7d22dda112a3c18ed57e8c061d95e51915980417
O=$EV/LEAK_SCAN_$L.json
T=("$LEAK_WT/research/06_scope_redesign/p1_v3_20261102/hpc_v31" "$LEAK_WT/research/06_scope_redesign/p1_v3_20261102/batch_def" "$LEAK_WT/research/06_scope_redesign/p1_hpr_20261027/hpc_package_src"
   /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105 /home/jin/v3fix)
[ -d "$PKGD" ] && T+=("$PKGD")
[ -d "$LEAK_WT/research/06_scope_redesign/p1_v3_fix_20261105" ] && T+=("$LEAK_WT/research/06_scope_redesign/p1_v3_fix_20261105")
/home/jin/miniforge3/envs/pypsa-earth/bin/python "$S/leak_scan_v3.py" "$O" "${T[@]}" > "$EV/leak_scan_$L.out" 2>&1
echo "LEAK_SCAN_EXIT=$?"
/home/jin/miniforge3/envs/pypsa-earth/bin/python -I -c "
import json, sys
r = json.load(open(sys.argv[1]))
print('clean', r.get('clean'), 'secret_values', r['n_secret_values'], 'patterns', r['patterns_supplied'], 'commits', r.get('n_commits'))
for t, v in r['targets'].items(): print(t.split('/')[-1], 'files', v['files'], 'hit_files', [(h['file'], h['value_hits'], h['pattern_hits']) for h in v['hits']][:12], 'excluded', len(v['excluded']))
print('commits_with_hits', {k[:8]: (v['value_hits'], v['pattern_hits'], v['files'][:6]) for k, v in r['commits'].items() if v['value_hits'] or v['pattern_hits']})
" "$O"
/home/jin/miniforge3/envs/pypsa-earth/bin/python "$S/leak_classify.py" "$O" "$PF" "$LEAK_WT" > "$EV/LEAK_CLASSIFY_$L.txt" 2>&1
echo "classified lines: $(wc -l < "$EV/LEAK_CLASSIFY_$L.txt")"
