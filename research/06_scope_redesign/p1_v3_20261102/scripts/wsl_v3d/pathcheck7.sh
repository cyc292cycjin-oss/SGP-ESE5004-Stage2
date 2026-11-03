#!/bin/bash
# V3 supplement 07 (review EVDIAG section 2.1 item 4): solve and post-solve chain on the rebuilt DAILY networks with HiGHS, first 8 days (8 x 24 h snapshots; no Gurobi, no licence, no WLS session).
# Read only: the chain runs, the EV morning floor holds in the solution, the ledger closes. No economic reading. V1 integrated, V2 no_new_xb (batch reference, B6, M12 benefit), V3 disconnected.
set -u
WT=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj
NETS=$MAIN/results_project/v3/builds_dmax; RUN=$MAIN/results_project/v3/path_check7; ST=$RUN/STATUS.txt; N=8
[ ! -e $RUN ] || { echo "REFUSED: $RUN exists"; exit 2; }
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[p]ytest')" = 0 ] || { echo "REFUSED: another solve or pytest is running"; exit 2; }
mkdir -p $RUN; cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
log START "commit=$(git rev-parse --short HEAD):dirty=$(git status --porcelain --untracked-files=no scripts_project | wc -l):solver=highs:truncate=$N:resolution=365_24h"
for spec in "integrated integrated $NETS/integrated/integrated_365_24h_unsolved.nc integrated" "no_new_xb no_new_xb $NETS/no_new_xb/no_new_xb_365_24h_unsolved.nc integrated" "disconnected disconnected $NETS/disconnected/disconnected_365_24h_unsolved.nc disconnected"; do
  set -- $spec; rid=$1; sc=$2; net=$3; ct=$4; dir=$RUN/$rid; mkdir -p $dir
  GRB_LICENSE_FILE=/nonexistent timeout -k 60 2400 /usr/bin/time -v "$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario $sc --output "$dir" --label SMOKE_TEST_ONLY --authorization "V3 supplement 07 daily path check, HiGHS, no Gurobi" \
    --solver highs --highs-ipm --time-limit 1800 --costs-table "$NETS/$ct/costs_active_research.csv" --truncate $N > $dir/solve.log 2> $dir/solve.err
  log END_$rid "exit=$?:$(grep -h 'Maximum resident' $dir/solve.err | tr -s ' ')"
  "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --out $dir/VIOLATIONS.json --truncate $N > $dir/c1_violations.log 2>&1; log VIOLATIONS_$rid "exit=$?"
  "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --violations $dir/VIOLATIONS.json --truncate $N > $dir/c1_precision.log 2>&1; log C1_$rid "exit=$?"
  "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir $dir --scenario $sc --label SMOKE_$rid --out $dir --register > $dir/m12.log 2>&1; log M12_$rid "exit=$?"
  "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario $sc --solve-dir $dir --allocation $dir/ALLOCATION.json --tag SMOKE_$rid --out $dir/m12_owen --register-dir $dir --truncate $N > $dir/m12_owen.log 2>&1; log OWEN_$rid "exit=$?"
done
"$PY" scripts_project/s4o_c1_precision.py reference --integrated $RUN/integrated --disconnected $RUN/no_new_xb --out $RUN/BATCH_REFERENCE.json > $RUN/c1_reference.log 2>&1; log BATCH_REFERENCE "exit=$?"
for spec in "integrated --build-receipt $NETS/integrated/integrated_BUILD_RECEIPT.json" "no_new_xb --registered-sha256 $(sha256sum $NETS/no_new_xb/no_new_xb_365_24h_unsolved.nc | cut -d' ' -f1)" "disconnected --registered-sha256 $(sha256sum $NETS/disconnected/disconnected_365_24h_unsolved.nc | cut -d' ' -f1)"; do
  set -- $spec; rid=$1; shift
  "$PY" scripts_project/s4o_c1_precision.py regrade --solve-dir $RUN/$rid --reference $RUN/BATCH_REFERENCE.json > $RUN/$rid/c1_regrade.log 2>&1; log REGRADE_$rid "exit=$?"
  "$PY" scripts_project/m12_rhs_audit.py regrade --owen $RUN/$rid/m12_owen/OWEN.json --precision $RUN/$rid/PRECISION.json --out $RUN/$rid/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json > $RUN/$rid/m12_owen_regrade.log 2>&1; log OWEN_REGRADE_$rid "exit=$?"
  lab=$("$PY" scripts_project/v5/gates_v6.py accept --solve-dir $RUN/$rid "$@" --repo . --out $RUN/$rid/V6_ACCEPTANCE.json 2> $RUN/$rid/v6.err | tail -1); log V6_$rid "exit=$?:$lab"
  "$PY" scripts_project/m10_batch3_summary.py stop-class --dir $RUN/$rid > $RUN/$rid/stop_class.log 2>&1; log STOPCLASS_$rid "$(tail -1 $RUN/$rid/stop_class.log | cut -c1-120)"
done
"$PY" scripts_project/m12_allocation.py benefit --repo . --integrated $RUN/integrated --disconnected $RUN/no_new_xb --out $RUN/M12_BENEFIT > $RUN/m12_benefit.log 2>&1; log M12_BENEFIT "exit=$?"
"$PY" scripts_project/v3_screen_tables.py --out-dir $RUN --runs integrated,no_new_xb > $RUN/screen.log 2>&1; log SCREEN_TABLES "exit=$?:$(tail -1 $RUN/screen.log | cut -c1-120)"
log DONE
cut -c1-200 $ST
