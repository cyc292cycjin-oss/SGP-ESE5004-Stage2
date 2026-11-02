#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
OUT=$MAIN/results_project/v3/builds
cd $W/scripts_project
$PY v3_static.py --dir $OUT --v2 $MAIN/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc --out $W/research/06_scope_redesign/p1_v3_20261102 > $OUT/static3.log 2>&1
echo "STATIC3:$?" >> $OUT/BUILD_STATUS.txt
$PY /home/jin/v3/chk_st.py 2>&1 | head -7 | cut -c1-420
awk -F, 'NR>1 && ($3+0 != $4+0 || $3+0 != $5+0)' $W/research/06_scope_redesign/p1_v3_20261102/evidence/DEMAND_NETWORK_CHECK_V3.csv | awk -F, '{d=$3-$4; if (d<0) d=-d; if (d>1e-6) print}' | cut -c1-120
