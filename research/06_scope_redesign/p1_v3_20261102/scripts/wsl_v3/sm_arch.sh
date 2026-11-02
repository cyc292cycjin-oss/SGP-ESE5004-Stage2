#!/bin/bash
# archive the small smoke results in the deliverable folder (no logs, no LP or solution arrays), cost comparison table, unit tests
export PYTHONHASHSEED=0
P=/home/jin/miniforge3/envs/pypsa-earth/bin/python; R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
E=/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/smoke
cd /home/jin/wt_v3_20261102
for s in integrated no_new_xb; do
  mkdir -p $E/$s
  cp $R/v3/smoke_r2/$s/{SOLVE_RECEIPT.json,V5_GATES.json,V6_ACCEPTANCE.json,PRECISION.json,LEDGER_IDENTITY.json,STOP_CLASS.json,COUNTRY_COST_LEDGER.csv,ALLOCATION.csv} $E/$s/ 2>&1 | cut -c1-120
done
cp $R/v3/smoke_r2/STATUS.txt $E/STATUS.txt; cp $R/v3/smoke_r2/M12_BENEFIT/BENEFIT.csv $E/BENEFIT.csv; cp $R/v3/smoke_r2/BATCH_REFERENCE.json $E/
$P - <<'PY' 2>&1 | grep -v "PROJ\|Deprecation\|fullslice" | tail -3 | cut -c1-200
import re, runpy, sys
sys.argv = ["x"]
src = open("/home/jin/v3/sm_cmp.py").read()
src = src.replace('print(t.reindex(t.d.abs().sort_values(ascending=False).index).head(22).round(3).to_string())',
                  't.reindex(t.d.abs().sort_values(ascending=False).index).round(6).rename_axis("carrier").to_csv("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/smoke/V3_V2_COST_BY_CARRIER_56.csv")')
exec(compile(src, "sm_cmp", "exec"))
PY
$P -m pytest tests/research/test_v3.py -q --no-header -p no:cacheprovider -W ignore 2>&1 | tail -2 | cut -c1-120
$P /home/jin/v3/sm_ver.py 2>&1 | grep -v PROJ | cut -c1-300
du -sh $E | cut -f1; ls $E
