#!/bin/bash
# kill the duplicated (retry) disconnected solve started by runner v2; run the one remaining smoke (pc_disconnected) once under the 30-min stop-loss; no gap runs (none terminated exactly "infeasible")
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s3_7/gurobi
for p in $(pgrep -f "s2_solve.py --network results_project/s3_7/disconnected/"); do kill $p 2>/dev/null; done
sleep 3
echo "KILLED_DUPLICATE_RETRY_disconnected_v2:$(date -u +%Y-%m-%dT%H:%M:%SZ) (runner v2 restarted a run already made by runner v1; stopped per the no-retry rule; v1 result directory was overwritten before the stop)" >> $OUT/STATUS.txt
mv $OUT/smoke/disconnected $OUT/smoke/disconnected_v1_overwritten_by_v2_restart 2>/dev/null || true
tag=pc_disconnected; sc=disconnected
AUTH="decision 65 (user authorization 2026-10-16): Gurobi 12.0.3 WLS academic licence, 56x3h smoke producer_credit disconnected; stop-loss 30 min, no retry; smoke only"
mkdir -p $OUT/smoke/$tag
/usr/bin/time -v $PY scripts_project/s2_solve.py --network results_project/s3_7/$tag/${sc}_2920_3h_unsolved.nc --scenario $sc --output $OUT/smoke/$tag --truncate 56 --label SMOKE_TEST_ONLY --authorization "$AUTH" --solver gurobi --time-limit 1750 > $OUT/smoke/${tag}_solve.log 2> $OUT/smoke/${tag}_solve.err &
pid=$!; start=$(date +%s)
while kill -0 $pid 2>/dev/null; do
  sleep 15
  if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill $pid; sleep 5; kill -9 $pid 2>/dev/null; echo "KILLED_30MIN_$tag:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $OUT/STATUS.txt; fi
done
wait $pid 2>/dev/null
cond=$($PY -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('termination_condition','none'))" $OUT/smoke/$tag/SOLVE_RECEIPT.json 2>/dev/null || echo none)
echo "GSMOKE_$tag:$cond" >> $OUT/STATUS.txt
echo "DONE2" >> $OUT/STATUS.txt
