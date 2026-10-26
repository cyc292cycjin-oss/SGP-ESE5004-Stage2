#!/bin/bash
# DFX v3 phase 3 end: P6 rescan (pattern file outside the repo) -> evidence -> evidence JSON -> final commit -> push (never force) -> verify remote head.
set -u
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026
D=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
echo "== P6 rescan (working tree + commits)"; bash /home/jin/dfx3/p6_scan.sh | $PY -c "import json,sys; r=json.load(sys.stdin); print('clean', r['clean'], 'secret_values', r['n_secret_values']); [print(k.split('/')[-1], [(h[0], h[1], h[2]) for h in v['hits']]) for k, v in r['targets'].items()]; print('commits with hits:', {k: (v['value_hits'], v['pattern_hits'], [f.split('/')[-1] for f in v['files']]) for k, v in r['commits'].items()})"
cp $MAIN/leak_scan/P6_LEAK_SCAN.json $D/evidence/leak_scan/
echo "== evidence json"; $PY /home/jin/dfx3/make_evidence.py $W/cloud_package_dfx $MAIN/tests/full.log | head -3
echo "== commit"; bash /home/jin/dfx3/commit.sh /home/jin/dfx3/msg_phase3.txt 2>&1 | tail -3
echo "== push"; bash /home/jin/dfx3/push.sh
