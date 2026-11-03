#!/bin/bash
# V3 HPC package step 3 (instruction V14 section 3; at most 2 local Gurobi calls, >= 330 s apart, no retry, no parameter change): first 56 snapshots of the
# F1 / F2 2920x3h networks (S-A shipping, decision 187), serial: integrated, no_new_xb; profile formal_barrier_1e6_t16 (Threads 16), Gurobi TimeLimit 3,000 s,
# wall cap 3,600 s (process group killed) - the same path and settings as the supplement 05 smoke (smoke_s5.sh), only the networks differ.
# User 2026-11-04: smoke starts directly, WLS session free, AnyConnect disconnected - a bare TCP connect to the token server (no data, no licence) still
# comes before every solve; a run without a returned solution stops the batch. Afterwards (no licence): violations -> C1 -> M12 -> Owen ->
# reference / regrade / benefit -> GATES_V6 -> stop-class -> v3_smoke_eval. Licence only through GRB_LICENSE_FILE for the solve (never read, never copied);
# solve.log / solve.err stay in results_project.
set -u
WT=/home/jin/wt_v3_hpc; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
E2=$MAIN/results_project/v3hpc/builds/sa; RUN=$MAIN/results_project/v3hpc/smoke_hpc; ST=$RUN/STATUS.txt
EV=$WT/research/06_scope_redesign/p1_v3_20261102/evidence/hpc/smoke
LIC=/home/jin/gurobi.lic; TL=3000; WALL=3600; GAP=330; GRACE=60; N=56; PROFILE=formal_barrier_1e6_t16
[ "${1:-}" = "--confirmed" ] || { echo "REFUSED: needs --confirmed <time> (user statement that the WLS session is free and AnyConnect disconnected)"; exit 5; }
AUTH="V3 HPC package step 3 (user 2026-11-04: smoke starts directly, WLS session free, AnyConnect disconnected; ${2:?time}): local 56-snapshot smoke of F1 / F2 (S-A shipping), integrated and no_new_xb, profile $PROFILE, TimeLimit $TL s, wall cap $WALL s, no retry"
[ ! -e $RUN/integrated/SOLVE_RECEIPT.json ] || { echo "REFUSED: $RUN holds a previous smoke"; exit 2; }
mkdir -p $RUN; cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[g]urobi_cl|[b]4_split_solve\.py|[s]2_network\.py|[c]hk_f\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
alive() { [ -n "$(pgrep -g "$1" 2>/dev/null)" ]; }
token_route() { timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null; }
[ -f "$LIC" ] || { log NO_LICENCE_FILE; exit 3; }   # existence only
token_route || { log NO_TOKEN_ROUTE "token server not reachable from WSL (AnyConnect?) - not started"; exit 6; }
[ "$(busy)" = 0 ] || { log SOLVER_BUSY "$(busy) processes - not started"; exit 4; }
[ "$(ps -eo args= | grep -c '[p]ytest')" = 0 ] || { log PYTEST_RUNNING "stand-in tests must not run during a real solve - not started"; exit 4; }
D=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l); [ "$D" = 0 ] || { log DIRTY "$D tracked changes - not started"; exit 2; }
log START "commit=$(git rev-parse HEAD):profile=$PROFILE:truncate=$N:time_limit=$TL:wall_cap=$WALL:networks=$(sha256sum $E2/integrated/integrated_2920_3h_unsolved.nc | cut -c1-12),$(sha256sum $E2/no_new_xb/no_new_xb_2920_3h_unsolved.nc | cut -c1-12)"
for spec in "integrated integrated $E2" "no_new_xb no_new_xb $E2"; do
  set -- $spec; rid=$1; sc=$2; nd=$3
  dir=$RUN/$rid; net=$nd/$sc/${sc}_2920_3h_unsolved.nc; mkdir -p $dir
  if [ -f $dir/SOLVE_RECEIPT.json ]; then log SKIP_EXISTING_$rid "no re-solve"; continue; fi
  if [ -f $RUN/.last_solve_end ]; then
    last=$(cat $RUN/.last_solve_end); while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done; log GAP_$rid "$(( $(date +%s) - last ))s"
  fi
  [ "$(busy)" = 0 ] || { log SOLVER_BUSY_$rid "$(busy) processes - stop"; break; }
  token_route || { log NO_TOKEN_ROUTE_$rid "token server not reachable from WSL - stop"; break; }
  cmd=("$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario $sc --output "$dir" --label SMOKE_TEST_ONLY --authorization "$AUTH; run $rid"
       --solver gurobi --solver-profile $PROFILE --scaling on --time-limit $TL --costs-table "$nd/integrated/costs_active_research.csv" --truncate $N)
  ( exec setsid env GRB_LICENSE_FILE=$LIC /usr/bin/time -v "${cmd[@]}" > $dir/solve.log 2> $dir/solve.err ) &
  pid=$!; t0=$(date +%s); sleep 1; pg=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  log SOLVE_$rid "pid=$pid:pgid=$pg"
  while kill -0 $pid 2>/dev/null; do
    sleep 5
    if [ $(( $(date +%s) - t0 )) -ge $WALL ]; then
      log KILLED_${WALL}S_$rid; kill -TERM -- "-$pg" 2>/dev/null; g=0
      while alive $pg && [ $g -lt $GRACE ]; do sleep 1; g=$((g + 1)); done
      alive $pg && { kill -KILL -- "-$pg" 2>/dev/null; log KILL9_$rid; }
      break
    fi
  done
  wait $pid 2>/dev/null; rc=$?; date +%s > $RUN/.last_solve_end
  cond=$("$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('termination_condition','none'), r.get('status','none'), r.get('objective', r.get('objective_value','')))" $dir/SOLVE_RECEIPT.json 2>/dev/null || echo "no_receipt")
  log END_$rid "exit=$rc:$(( $(date +%s) - t0 ))s:$cond:$(grep -h 'Maximum resident' $dir/solve.err | awk '{printf "%.2fGiB", $NF/1048576}')"
  [ -f $dir/solution/X.npy ] || { log STOP_NO_SOLUTION_$rid "no returned solution - the remaining runs are not started"; break; }
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --out $dir/VIOLATIONS.json --truncate $N > $dir/c1_violations.log 2>&1 ); log VIOLATIONS_$rid "exit=$?"
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --violations $dir/VIOLATIONS.json --truncate $N > $dir/c1_precision.log 2>&1 ); log C1_$rid "exit=$?"
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir $dir --scenario $sc --label SMOKE_$rid --out $dir --register > $dir/m12.log 2>&1 ); log M12_$rid "exit=$?"
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario $sc --solve-dir $dir --allocation $dir/ALLOCATION.json --tag SMOKE_$rid --out $dir/m12_owen --register-dir $dir --truncate $N > $dir/m12_owen.log 2>&1 ); log OWEN_$rid "exit=$?"
done
for pair in "integrated no_new_xb BATCH_REFERENCE.json M12_BENEFIT"; do
  set -- $pair; a=$1; b=$2; ref=$3; ben=$4
  if [ -f $RUN/$a/COUNTRY_COST_LEDGER.csv ] && [ -f $RUN/$b/COUNTRY_COST_LEDGER.csv ]; then
    env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py reference --integrated $RUN/$a --disconnected $RUN/$b --out $RUN/$ref > $RUN/c1_$ref.log 2>&1; log REFERENCE_$a "exit=$?"
    for rid in $a $b; do
      env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py regrade --solve-dir $RUN/$rid --reference $RUN/$ref > $RUN/$rid/c1_regrade.log 2>&1; log REGRADE_$rid "exit=$?"
      [ -f $RUN/$rid/m12_owen/OWEN.json ] && { env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_rhs_audit.py regrade --owen $RUN/$rid/m12_owen/OWEN.json --precision $RUN/$rid/PRECISION.json --out $RUN/$rid/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json > $RUN/$rid/m12_owen_regrade.log 2>&1; log OWEN_REGRADE_$rid "exit=$?"; }
    done
    env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py benefit --repo . --integrated $RUN/$a --disconnected $RUN/$b --out $RUN/$ben > $RUN/$ben.log 2>&1; log ${ben} "exit=$?:$(tail -1 $RUN/$ben.log | cut -c1-200)"
  else
    log REFERENCE_$a "missing ledgers"
  fi
done
for spec in "integrated integrated $E2" "no_new_xb no_new_xb $E2"; do
  set -- $spec; rid=$1; sc=$2; nd=$3
  [ -f $RUN/$rid/SOLVE_RECEIPT.json ] || continue
  if [ $sc = integrated ]; then reg=(--build-receipt $nd/integrated/integrated_BUILD_RECEIPT.json); else reg=(--registered-sha256 $(sha256sum $nd/no_new_xb/no_new_xb_2920_3h_unsolved.nc | cut -d' ' -f1)); fi
  lab=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/v5/gates_v6.py accept --solve-dir $RUN/$rid "${reg[@]}" --repo . --out $RUN/$rid/V6_ACCEPTANCE.json 2> $RUN/$rid/v6.err | tail -1); log V6_$rid "$lab"
  env -u GRB_LICENSE_FILE "$PY" scripts_project/m10_batch3_summary.py stop-class --dir $RUN/$rid > $RUN/$rid/stop_class.log 2>&1; log STOPCLASS_$rid "$(tail -1 $RUN/$rid/stop_class.log)"
done
mkdir -p $EV
env -u GRB_LICENSE_FILE "$PY" scripts_project/v3_smoke_eval.py --run $RUN --out $EV --v2-run $MAIN/results_project/dfx_v3/smoke_v2 > $RUN/eval.log 2>&1; log EVAL "exit=$?"
env -u GRB_LICENSE_FILE "$PY" scripts_project/v3_screen_tables.py --out-dir $RUN --runs integrated,no_new_xb > $RUN/screen.log 2>&1; log SCREEN_TABLES "exit=$?"
log DONE
