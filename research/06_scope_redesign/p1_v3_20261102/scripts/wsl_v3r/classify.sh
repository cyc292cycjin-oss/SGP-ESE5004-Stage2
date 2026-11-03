#!/bin/bash
# V3 screening rerun (supplement 07): classify the hits of LEAK_SCAN_<label>.json (files and commits) with classify_v3.py; the instance name is read from the instance into a
# variable (never printed, never written). Host / port only from the environment.
#   wsl env V3S_HOST=.. V3S_PORT=.. bash classify.sh [label]
set -u
source /home/jin/v3r/ssh.sh
INST=$(v3s_ssh hostname 2>/dev/null | tr -d '\r\n '); [ ${#INST} -gt 8 ] || { echo "instance name not read - refused"; exit 2; }
J=/home/jin/v3r/records/LEAK_SCAN_${1:-pre}.json
ARGS=$(/home/jin/miniforge3/envs/pypsa-earth/bin/python -I -c "
import json, sys
r = json.load(open(sys.argv[1])); a = []
for t, v in r['targets'].items():
    a += [t + '/' + h['file'] for h in v['hits']]
a += ['commit:' + k for k, v in r['commits'].items() if v['value_hits'] or v['pattern_hits']]
print(' '.join(a))
" $J)
cd /home/jin/wt_v3_20261102
V3S_INST="$INST" /home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/v3r/classify_v3.py $ARGS 2>&1 | cut -c1-260
