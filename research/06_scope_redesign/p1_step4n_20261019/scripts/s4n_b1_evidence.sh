#!/bin/bash
# S4N supplement 01 B1.2 evidence: copy the local probe outputs (light files) to the work folder and scan them for licence strings.
set -u
P=/home/jin/s4n_local/pkg/probe/20261019T061431Z_449
E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/evidence/s4n_b1
mkdir -p $E
cp $P/SPEED_PROBE.json $P/STATUS.txt $P/GUROBI_LOG_SCRUBBED.txt $E/
cp $P/solve/SOLVE_RECEIPT.json $E/ 2>/dev/null
cp /home/jin/s4n_local/probe_local_console.log $E/
cp /home/jin/s4n_b1_probe_local.sh $E/RUN_SCRIPT_s4n_b1_probe_local.sh
cp /home/jin/s4n_b1_envlock.sh $E/RUN_SCRIPT_s4n_b1_envlock.sh
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $E)
[ -z "$H" ] && echo "LICENCE_SCAN_EVIDENCE: no hit ($(ls $E | wc -l) files)" || { echo "LICENCE STRING FOUND:"; echo "$H"; }
/home/jin/miniforge3/envs/pypsa-earth/bin/python -c "import json,sys; r=json.load(open(sys.argv[1])); r.pop('reference'); print(json.dumps(r))" $P/SPEED_PROBE.json
grep -m1 "Optimize a model" $P/GUROBI_LOG_SCRUBBED.txt; grep -m1 "^Presolved" $P/GUROBI_LOG_SCRUBBED.txt; grep -m1 "Barrier solved" $P/GUROBI_LOG_SCRUBBED.txt
/home/jin/miniforge3/envs/pypsa-earth/bin/python -c "import json,sys; r=json.load(open(sys.argv[1])); print('lp', r.get('lp',{}).get('num_row'), r.get('lp',{}).get('num_col'), r.get('lp',{}).get('nnz'), 'gates_tol', (r.get('gates') or {}).get('all_passed_solver_tolerances'), 'truncated_to', r['input_network'].get('truncated_to'))" $P/solve/SOLVE_RECEIPT.json
