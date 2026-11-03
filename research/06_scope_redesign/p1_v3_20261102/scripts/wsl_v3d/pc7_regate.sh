#!/bin/bash
# V3 supplement 07: GATES_V6 of the integrated daily path-check run again, against the registered 365x24h SHA256 instead of the build receipt (whose network entry is the 2920x3h file): no solve,
# written beside the first verdict (V6_ACCEPTANCE.json kept). Then the read-out chk_pc7.py.
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj
WT=/home/jin/wt_v3_20261102; RUN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/path_check7; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $WT || exit 1
lab=$("$PY" scripts_project/v5/gates_v6.py accept --solve-dir $RUN/integrated --registered-sha256 a0273602016003fc4318cdd993b69716772c700cd2f9d079059fabcdde099c8b --repo . --out $RUN/integrated/V6_ACCEPTANCE_REGISTERED_365.json 2> $RUN/integrated/v6_registered.err | tail -1)
echo "V6_integrated_registered_365:exit=$?:$lab" | tee -a $RUN/STATUS.txt
"$PY" /home/jin/v3d/chk_pc7.py $RUN $WT/research/06_scope_redesign/p1_v3_20261102/evidence/dmax 2>&1 | grep -v Warning
