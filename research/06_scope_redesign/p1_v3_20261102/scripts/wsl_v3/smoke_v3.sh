#!/bin/bash
# V3 phase 3 item 4 (instruction: at most 2 local Gurobi calls, truncated v3 networks, <= 60 min each, >= 330 s apart, no retry, no parameter change, user confirmation that the WLS session is free before the call):
# 2920x3h v3 networks of results_project/v3/builds truncated to the first 56 snapshots, integrated and no_new_xb once each, profile A formal_barrier (Threads 8), Gurobi TimeLimit 3,000 s, wall cap 3,600 s
# per run (process group killed), serial. Afterwards (no licence): violations -> C1 (provisional, then batch reference + regrade) -> M12 allocation -> Owen dual form -> GATES_V6 -> stop-class -> v3_smoke_eval.
# Licence only through GRB_LICENSE_FILE for the solve (never read, never copied). Output of the solve is scrubbed by s2_solve into GUROBI_LOG_SCRUBBED.txt; solve.log / solve.err stay in results_project.
set -u
WT=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
NETS=$MAIN/results_project/v3/builds; RUN=$MAIN/results_project/v3/smoke; ST=$RUN/STATUS.txt
EV=$WT/research/06_scope_redesign/p1_v3_20261102/evidence/smoke
LIC=/home/jin/gurobi.lic; TL=3000; WALL=3600; GAP=330; GRACE=60; N=56; PROFILE=formal_barrier
AUTH="V3 phase 3 item 4 (user confirmation WLS session free __CONFIRMED__): local 56-snapshot smoke on the v3 2920x3h networks, integrated + no_new_xb once each, profile formal_barrier, TimeLimit 3000 s, wall cap 3600 s, no retry"
[ "${1:-}" = "--confirmed" ] || { echo "REFUSED: needs --confirmed <time>, given only after the user confirmed the WLS session is free"; exit 5; }
AUTH=${AUTH/__CONFIRMED__/${2:?time of the confirmation}}
mkdir -p $RUN; cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[g]urobi_cl|[b]4_split_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
alive() { [ -n "$(pgrep -g "$1" 2>/dev/null)" ]; }
[ -f "$LIC" ] || { log NO_LICENCE_FILE; exit 3; }   # existence only
[ "$(busy)" = 0 ] || { log SOLVER_BUSY "$(busy) processes - not started"; exit 4; }
[ "$(ps -eo args= | grep -c '[p]ytest')" = 0 ] || { log PYTEST_RUNNING "stand-in tests must not run during a real solve - not started"; exit 4; }
D=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l); [ "$D" = 0 ] || { log DIRTY "$D tracked changes - not started"; exit 2; }
log START "commit=$(git rev-parse HEAD):profile=$PROFILE:truncate=$N:time_limit=$TL:wall_cap=$WALL:networks=builds"
for sc in integrated no_new_xb; do
  dir=$RUN/$sc; net=$NETS/$sc/${sc}_2920_3h_unsolved.nc; mkdir -p $dir
  if [ -f $dir/SOLVE_RECEIPT.json ]; then log SKIP_EXISTING_$sc "no re-solve"; continue; fi
  if [ -f $RUN/.last_solve_end ]; then
    last=$(cat $RUN/.last_solve_end); while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done; log GAP_$sc "$(( $(date +%s) - last ))s"
  fi
  [ "$(busy)" = 0 ] || { log SOLVER_BUSY_$sc "$(busy) processes - stop"; break; }
  cmd=("$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario $sc --output "$dir" --label SMOKE_TEST_ONLY --authorization "$AUTH; run $sc"
       --solver gurobi --solver-profile $PROFILE --scaling on --time-limit $TL --costs-table "$NETS/integrated/costs_active_research.csv" --truncate $N)
  ( exec setsid env GRB_LICENSE_FILE=$LIC /usr/bin/time -v "${cmd[@]}" > $dir/solve.log 2> $dir/solve.err ) &
  pid=$!; t0=$(date +%s); sleep 1; pg=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  log SOLVE_$sc "pid=$pid:pgid=$pg"
  while kill -0 $pid 2>/dev/null; do
    sleep 5
    if [ $(( $(date +%s) - t0 )) -ge $WALL ]; then
      log KILLED_${WALL}S_$sc; kill -TERM -- "-$pg" 2>/dev/null; g=0
      while alive $pg && [ $g -lt $GRACE ]; do sleep 1; g=$((g + 1)); done
      alive $pg && { kill -KILL -- "-$pg" 2>/dev/null; log KILL9_$sc; }
      break
    fi
  done
  wait $pid 2>/dev/null; rc=$?; date +%s > $RUN/.last_solve_end
  cond=$("$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('termination_condition','none'), r.get('status','none'), r.get('objective', r.get('objective_value','')))" $dir/SOLVE_RECEIPT.json 2>/dev/null || echo "no_receipt")
  log END_$sc "exit=$rc:$(( $(date +%s) - t0 ))s:$cond:$(grep -h 'Maximum resident' $dir/solve.err | awk '{printf "%.2fGiB", $NF/1048576}')"
  if [ -f $dir/solution/X.npy ]; then
    ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY \
        --out $dir/VIOLATIONS.json --truncate $N > $dir/c1_violations.log 2> $dir/c1_violations.err ); log VIOLATIONS_$sc "exit=$?"
  fi
  ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY \
      --violations $dir/VIOLATIONS.json --truncate $N > $dir/c1_precision.log 2> $dir/c1_precision.err ); log C1_$sc "exit=$?"
  ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir $dir --scenario $sc --label SMOKE_$sc --out $dir --register > $dir/m12.log 2> $dir/m12.err ); log M12_$sc "exit=$?"
  ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario $sc --solve-dir $dir --allocation $dir/ALLOCATION.json \
      --tag SMOKE_$sc --out $dir/m12_owen --register-dir $dir --truncate $N > $dir/m12_owen.log 2> $dir/m12_owen.err ); log OWEN_$sc "exit=$?"
done
if [ -f $RUN/integrated/COUNTRY_COST_LEDGER.csv ] && [ -f $RUN/no_new_xb/COUNTRY_COST_LEDGER.csv ]; then
  env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py reference --integrated $RUN/integrated --disconnected $RUN/no_new_xb --out $RUN/BATCH_REFERENCE.json > $RUN/c1_reference.log 2>&1
  log BATCH_REFERENCE "exit=$?"
  for sc in integrated no_new_xb; do
    env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py regrade --solve-dir $RUN/$sc --reference $RUN/BATCH_REFERENCE.json > $RUN/$sc/c1_regrade.log 2>&1; log REGRADE_$sc "exit=$?"
    [ -f $RUN/$sc/m12_owen/OWEN.json ] && { env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_rhs_audit.py regrade --owen $RUN/$sc/m12_owen/OWEN.json --precision $RUN/$sc/PRECISION.json --out $RUN/$sc/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json > $RUN/$sc/m12_owen_regrade.log 2>&1; log OWEN_REGRADE_$sc "exit=$?"; }
  done
else
  log BATCH_REFERENCE "missing ledgers"
fi
for sc in integrated no_new_xb; do
  if [ $sc = integrated ]; then reg=(--build-receipt $NETS/integrated/integrated_BUILD_RECEIPT.json); else reg=(--registered-sha256 $(sha256sum $NETS/no_new_xb/no_new_xb_2920_3h_unsolved.nc | cut -d' ' -f1)); fi
  lab=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/v5/gates_v6.py accept --solve-dir $RUN/$sc "${reg[@]}" --repo . --out $RUN/$sc/V6_ACCEPTANCE.json 2> $RUN/$sc/v6.err | tail -1)
  log V6_$sc "$lab"
  env -u GRB_LICENSE_FILE "$PY" scripts_project/m10_batch3_summary.py stop-class --dir $RUN/$sc > $RUN/$sc/stop_class.log 2>&1; log STOPCLASS_$sc "$(tail -1 $RUN/$sc/stop_class.log)"
done
if [ -f $RUN/integrated/ALLOCATION.json ] && [ -f $RUN/no_new_xb/ALLOCATION.json ]; then
  env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py benefit --repo . --integrated $RUN/integrated --disconnected $RUN/no_new_xb --out $RUN/M12_BENEFIT > $RUN/m12_benefit.log 2>&1; log M12_BENEFIT "exit=$?:$(tail -1 $RUN/m12_benefit.log | cut -c1-200)"
fi
mkdir -p $EV
env -u GRB_LICENSE_FILE "$PY" scripts_project/v3_smoke_eval.py --run $RUN --out $EV --v2-run $MAIN/results_project/dfx_v3/smoke_v2 > $RUN/eval.log 2>&1; log EVAL "exit=$?"
log DONE
