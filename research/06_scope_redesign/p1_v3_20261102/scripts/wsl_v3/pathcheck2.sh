#!/bin/bash
# V3 RUN_PLAN section 6, second pass: both scenarios through the whole post-solve chain with HiGHS on the first 8 snapshots (no Gurobi, no licence, no WLS session). Only whether the chain runs is read.
set -u
WT=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
NETS=$MAIN/results_project/v3/builds; RUN=$MAIN/results_project/v3/path_check2; ST=$RUN/STATUS.txt; N=8
rm -rf $RUN; mkdir -p $RUN; cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
log START "commit=$(git rev-parse --short HEAD):dirty=$(git status --porcelain --untracked-files=no scripts_project | wc -l):solver=highs:truncate=$N"
for sc in integrated no_new_xb; do
  dir=$RUN/$sc; net=$NETS/$sc/${sc}_2920_3h_unsolved.nc; mkdir -p $dir
  GRB_LICENSE_FILE=/nonexistent timeout -k 60 2000 "$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario $sc --output "$dir" --label SMOKE_TEST_ONLY --authorization "V3 RUN_PLAN section 6 code path check, HiGHS, no Gurobi" \
    --solver highs --highs-ipm --time-limit 1800 --costs-table "$NETS/integrated/costs_active_research.csv" --truncate $N > $dir/solve.log 2> $dir/solve.err
  log END_$sc "exit=$?"
  "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --out $dir/VIOLATIONS.json --truncate $N > $dir/c1_violations.log 2>&1; log VIOLATIONS_$sc "exit=$?"
  "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --violations $dir/VIOLATIONS.json --truncate $N > $dir/c1_precision.log 2>&1; log C1_$sc "exit=$?"
  "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir $dir --scenario $sc --label SMOKE_$sc --out $dir --register > $dir/m12.log 2>&1; log M12_$sc "exit=$?"
  "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario $sc --solve-dir $dir --allocation $dir/ALLOCATION.json --tag SMOKE_$sc --out $dir/m12_owen --register-dir $dir --truncate $N > $dir/m12_owen.log 2>&1; log OWEN_$sc "exit=$?"
done
"$PY" scripts_project/s4o_c1_precision.py reference --integrated $RUN/integrated --disconnected $RUN/no_new_xb --out $RUN/BATCH_REFERENCE.json > $RUN/c1_reference.log 2>&1; log BATCH_REFERENCE "exit=$?"
for sc in integrated no_new_xb; do
  "$PY" scripts_project/s4o_c1_precision.py regrade --solve-dir $RUN/$sc --reference $RUN/BATCH_REFERENCE.json > $RUN/$sc/c1_regrade.log 2>&1; log REGRADE_$sc "exit=$?"
  "$PY" scripts_project/m12_rhs_audit.py regrade --owen $RUN/$sc/m12_owen/OWEN.json --precision $RUN/$sc/PRECISION.json --out $RUN/$sc/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json > $RUN/$sc/m12_owen_regrade.log 2>&1; log OWEN_REGRADE_$sc "exit=$?"
  if [ $sc = integrated ]; then reg=(--build-receipt $NETS/integrated/integrated_BUILD_RECEIPT.json); else reg=(--registered-sha256 $(sha256sum $NETS/no_new_xb/no_new_xb_2920_3h_unsolved.nc | cut -d' ' -f1)); fi
  lab=$("$PY" scripts_project/v5/gates_v6.py accept --solve-dir $RUN/$sc "${reg[@]}" --repo . --out $RUN/$sc/V6_ACCEPTANCE.json 2> $RUN/$sc/v6.err | tail -1); log V6_$sc "exit=$?:$lab"
  "$PY" scripts_project/m10_batch3_summary.py stop-class --dir $RUN/$sc > $RUN/$sc/stop_class.log 2>&1; log STOPCLASS_$sc "$(tail -1 $RUN/$sc/stop_class.log | cut -c1-120)"
done
"$PY" scripts_project/m12_allocation.py benefit --repo . --integrated $RUN/integrated --disconnected $RUN/no_new_xb --out $RUN/M12_BENEFIT > $RUN/m12_benefit.log 2>&1; log M12_BENEFIT "exit=$?"
"$PY" scripts_project/v3_smoke_eval.py --run $RUN --out $RUN/eval --v2-run $MAIN/results_project/dfx_v3/smoke_v2 > $RUN/eval.log 2>&1; log EVAL "exit=$?"
log DONE
cut -c1-200 $ST
tail -25 $RUN/eval.log | cut -c1-200
