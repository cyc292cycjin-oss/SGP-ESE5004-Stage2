#!/bin/bash
export PYTHONHASHSEED=0
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
cd /home/jin/v3h && env -u GRB_LICENSE_FILE $PY chk_f.py $MAIN/results_project/v3/builds_op $MAIN/results_project/v3hpc/builds /home/jin/wt_v3_hpc $MAIN/results_project/v3hpc/evidence 2>&1 | grep -v Warning | tail -5
for r in sa sa_ev05; do $PY -c "import json,sys; d=json.load(open(sys.argv[1])); print(sys.argv[2], 'all_structural_passed', d.get('all_structural_passed'))" $MAIN/results_project/v3hpc/builds/$r/static/V3_STATIC_CHECK.json $r 2>/dev/null || ls $MAIN/results_project/v3hpc/builds/$r/static; done
for r in sa sa_ev05; do $PY -c "import json,sys; d=json.load(open(sys.argv[1])); print(sys.argv[2], 'all_structural_passed', d.get('all_structural_passed'), {k: (v.get('passed') if isinstance(v, dict) else None) for k, v in d.items() if isinstance(v, dict) and 'passed' in v})" $MAIN/results_project/v3hpc/builds/$r/static/evidence/V3_STATIC_CHECK.json $r; done
