#!/bin/bash
# V3 supplement 07: the static check of build_s7.sh again, with the demand table it reads from its --out folder (first attempt: STATIC:1, FileNotFoundError on that table, before any check result)
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
OUT=$MAIN/results_project/v3/builds_dmax; D=$W/research/06_scope_redesign/p1_v3_20261102
cp $D/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v3.csv $OUT/static/
cd $W/scripts_project && $PY v3_static.py --dir $OUT --v2 $MAIN/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc --out $OUT/static > $OUT/static2.log 2>&1; RC=$?
echo "STATIC_RERUN:$RC:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $OUT/BUILD_STATUS.txt; echo "STATIC_RERUN exit $RC"
tail -3 $OUT/static2.log | cut -c1-300
$PY -c "import json,sys; d=json.load(open(sys.argv[1])); print('all_structural_passed', d.get('all_structural_passed'))" $OUT/static/evidence/V3_STATIC_CHECK.json
for f in V3_STATIC_CHECK.json DEMAND_NETWORK_CHECK_V3.csv X1_STOCK_TABLE_V3.csv SOURCE_LINKS_V3.csv; do cmp -s $OUT/static/evidence/$f $D/evidence/$f && echo "same as supplement 05: $f" || echo "differs from supplement 05: $f"; done
