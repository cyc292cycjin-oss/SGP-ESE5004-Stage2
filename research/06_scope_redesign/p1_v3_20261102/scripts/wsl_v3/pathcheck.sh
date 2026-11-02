#!/bin/bash
# V3 RUN_PLAN section 6: code path check with HiGHS on the first 8 snapshots of the integrated 2920x3h network (no Gurobi, no licence, no WLS session). Only whether the chain runs is read.
set -u
WT=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
NETS=$MAIN/results_project/v3/builds; RUN=$MAIN/results_project/v3/path_check; ST=$RUN/STATUS.txt; N=8; sc=integrated
rm -rf $RUN; mkdir -p $RUN/$sc; cd $WT || exit 1
net=$NETS/$sc/${sc}_2920_3h_unsolved.nc; dir=$RUN/$sc
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
log START "commit=$(git rev-parse --short HEAD):solver=highs:truncate=$N"
env -u GRB_LICENSE_FILE GRB_LICENSE_FILE=/nonexistent /usr/bin/time -v timeout -k 60 2000 "$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario $sc --output "$dir" --label SMOKE_TEST_ONLY --authorization "V3 RUN_PLAN section 6 code path check, HiGHS, no Gurobi" \
  --solver highs --highs-ipm --time-limit 1800 --costs-table "$NETS/$sc/costs_active_research.csv" --truncate $N > $dir/solve.log 2> $dir/solve.err
log END "exit=$?:$(grep -h 'Maximum resident' $dir/solve.err | awk '{printf "%.2fGiB", $NF/1048576}')"
"$PY" -c "
import json,sys
r=json.load(open(sys.argv[1]))
print({k:r.get(k) for k in ('status','termination_condition','objective','solve_seconds','stage')}, str(r.get('failure'))[:800])
" $dir/SOLVE_RECEIPT.json >> $ST 2>&1
if [ -f $dir/solution/X.npy ]; then
  env -u GRB_LICENSE_FILE "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --out $dir/VIOLATIONS.json --truncate $N > $dir/c1_violations.log 2>&1; log VIOLATIONS "exit=$?"
  env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --violations $dir/VIOLATIONS.json --truncate $N > $dir/c1_precision.log 2>&1; log C1 "exit=$?"
  env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir $dir --scenario $sc --label PATH_$sc --out $dir --register > $dir/m12.log 2>&1; log M12 "exit=$?"
  env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario $sc --solve-dir $dir --allocation $dir/ALLOCATION.json --tag PATH_$sc --out $dir/m12_owen --register-dir $dir --truncate $N > $dir/m12_owen.log 2>&1; log OWEN "exit=$?"
fi
log DONE
tail -14 $ST | cut -c1-900
