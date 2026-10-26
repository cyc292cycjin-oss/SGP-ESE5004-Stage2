#!/bin/bash
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; D=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
bash /home/jin/dfx3/p6_scan.sh | $PY -c "import json,sys; r=json.load(sys.stdin); print('clean', r['clean'], 'secret_values', r['n_secret_values']); [print(k.split('/')[-1], 'files', v['files'], 'hits', [(h[0], h[1], h[2]) for h in v['hits']]) for k, v in r['targets'].items()]; print('commits with hits:', {k: (v['value_hits'], v['pattern_hits'], [f.split('/')[-1] for f in v['files']]) for k, v in r['commits'].items()})"
cp $MAIN/results_project/dfx_v3/leak_scan/P6_LEAK_SCAN.json $D/evidence/leak_scan/ && echo "scan json copied to evidence/leak_scan/"
