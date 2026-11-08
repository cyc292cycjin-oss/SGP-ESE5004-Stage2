#!/bin/bash
# V4 D2c section 4 (V4_D2C_INSTRUCTION.md SHA 18f6e403; copy of the D2b scripts/smoke_d2b.sh): TWO local 56-snapshot solves, authorised by the instruction itself (section 0 /
# 4: "用户启动本指令即授权"), serial, at most one local Gurobi process, >= 330 s apart, no retry, no parameter change:
#   R1 v4d2c_F1  v4 main integrated (D2c build)          R2 v4d2c_F2  v4 main no_new_xb (derived from R1 build)
# Same path and settings as the v3.1 local smoke (smoke_h.sh): profile formal_barrier_1e6_t16 (Threads 16), --truncate 56, Gurobi TimeLimit 3,000 s,
# wall cap 3,600 s (process group killed), label SMOKE_TEST_ONLY. Before every solve: a bare TCP connect to the token server (no data, no licence).
# A run without a returned solution, or with a termination other than optimal, stops the remaining runs. Licence only through GRB_LICENSE_FILE
# for the solve (never read, never copied); raw solve.log / solve.err stay in results_project (licence lines; scrubbed copies for evidence).
set -u
WT=/home/jin/wt_v4_d2c; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
B=$MAIN/results_project/v4d2c/builds
RUN=$MAIN/results_project/v4d2c/smoke56; ST=$RUN/STATUS.txt
LIC=/home/jin/gurobi.lic; TL=3000; WALL=3600; GAP=330; GRACE=60; N=56; PROFILE=formal_barrier_1e6_t16
[ "${1:-}" = "--confirmed" ] || { echo "REFUSED: needs --confirmed <time>"; exit 5; }
AUTH="V4 D2c section 4 (V4_D2C_INSTRUCTION.md SHA 18f6e403, 2 local 56-snapshot solves authorised by starting the instruction; ${2:?time}): profile $PROFILE, TimeLimit $TL s, wall cap $WALL s, no retry"
mkdir -p $RUN; cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[g]urobi_cl|[b]4_split_solve\.py|[s]2_network\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
alive() { [ -n "$(pgrep -g "$1" 2>/dev/null)" ]; }
token_route() { timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null; }
[ -f "$LIC" ] || { log NO_LICENCE_FILE; exit 3; }
token_route || { log NO_TOKEN_ROUTE "token server not reachable from WSL (AnyConnect?) - not started"; exit 6; }
[ "$(busy)" = 0 ] || { log SOLVER_BUSY "$(busy) processes - not started"; exit 4; }
[ "$(ps -eo args= | grep -c '[p]ytest')" = 0 ] || { log PYTEST_RUNNING "not started"; exit 4; }
D=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l); [ "$D" = 0 ] || { log DIRTY "$D tracked changes - not started"; exit 2; }
SPECS=("v4d2c_F1 integrated $B/main/integrated/integrated_2920_3h_unsolved.nc $B/main/integrated/costs_active_research.csv"
       "v4d2c_F2 no_new_xb $B/main/no_new_xb/no_new_xb_2920_3h_unsolved.nc $B/main/integrated/costs_active_research.csv")
log START "commit=$(git rev-parse HEAD):profile=$PROFILE:truncate=$N:time_limit=$TL:wall_cap=$WALL"
for spec in "${SPECS[@]}"; do
  set -- $spec; rid=$1; sc=$2; net=$3; costs=$4
  dir=$RUN/$rid; mkdir -p $dir
  if [ -f $dir/SOLVE_RECEIPT.json ]; then log SKIP_EXISTING_$rid "no re-solve"; continue; fi
  if [ -f $RUN/.last_solve_end ]; then
    last=$(cat $RUN/.last_solve_end); while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done; log GAP_$rid "$(( $(date +%s) - last ))s"
  fi
  [ "$(busy)" = 0 ] || { log SOLVER_BUSY_$rid "$(busy) processes - stop"; break; }
  token_route || { log NO_TOKEN_ROUTE_$rid "token server not reachable from WSL - stop"; break; }
  log NETWORK_$rid "$(sha256sum $net | cut -c1-64)"
  cmd=("$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario $sc --output "$dir" --label SMOKE_TEST_ONLY --authorization "$AUTH; run $rid"
       --solver gurobi --solver-profile $PROFILE --scaling on --time-limit $TL --costs-table "$costs" --truncate $N)
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
  cond=$("$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('termination_condition','none'), r.get('status','none'), r.get('objective', ''))" $dir/SOLVE_RECEIPT.json 2>/dev/null || echo "no_receipt")
  log END_$rid "exit=$rc:$(( $(date +%s) - t0 ))s:$cond:$(grep -h 'Maximum resident' $dir/solve.err | awk '{printf "%.2fGiB", $NF/1048576}')"
  grep -viE 'licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic' $dir/solve.log > $dir/solve_log_scrubbed.txt
  [ -f $dir/solution/X.npy ] || { log STOP_NO_SOLUTION_$rid "no returned solution - the remaining runs are not started"; break; }
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --out $dir/VIOLATIONS.json --truncate $N > $dir/c1_violations.log 2>&1 ); log VIOLATIONS_$rid "exit=$?"
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir $dir --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --violations $dir/VIOLATIONS.json --truncate $N > $dir/c1_precision.log 2>&1 ); log C1_$rid "exit=$?"
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir $dir --scenario $sc --label SMOKE_$rid --out $dir --register > $dir/m12.log 2>&1 ); log M12_$rid "exit=$?"
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario $sc --solve-dir $dir --allocation $dir/ALLOCATION.json --tag SMOKE_$rid --out $dir/m12_owen --register-dir $dir --truncate $N > $dir/m12_owen.log 2>&1 ); log OWEN_$rid "exit=$?"
  if [ "$(echo $cond | cut -d' ' -f1)" != "optimal" ]; then log STOP_NOT_OPTIMAL_$rid "$cond - the remaining runs are not started (instruction section 4)"; break; fi
done
a=v4d2c_F1; b=v4d2c_F2
if [ -f $RUN/$a/COUNTRY_COST_LEDGER.csv ] && [ -f $RUN/$b/COUNTRY_COST_LEDGER.csv ]; then
  env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py reference --integrated $RUN/$a --disconnected $RUN/$b --out $RUN/BATCH_REFERENCE.json > $RUN/c1_reference.log 2>&1; log REFERENCE "exit=$?"
  for rid in $a $b; do
    env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py regrade --solve-dir $RUN/$rid --reference $RUN/BATCH_REFERENCE.json > $RUN/$rid/c1_regrade.log 2>&1; log REGRADE_$rid "exit=$?"
    [ -f $RUN/$rid/m12_owen/OWEN.json ] && { env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_rhs_audit.py regrade --owen $RUN/$rid/m12_owen/OWEN.json --precision $RUN/$rid/PRECISION.json --out $RUN/$rid/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json > $RUN/$rid/m12_owen_regrade.log 2>&1; log OWEN_REGRADE_$rid "exit=$?"; }
  done
  env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py benefit --repo . --integrated $RUN/$a --disconnected $RUN/$b --out $RUN/M12_BENEFIT > $RUN/M12_BENEFIT.log 2>&1; log M12_BENEFIT "exit=$?"
fi
for spec in "${SPECS[@]}"; do
  set -- $spec; rid=$1; sc=$2; net=$3
  [ -f $RUN/$rid/SOLVE_RECEIPT.json ] || continue
  rec=$(dirname $net)/${sc}_BUILD_RECEIPT.json
  if [ $sc = integrated ] && [ -f $rec ]; then reg=(--build-receipt $rec); else reg=(--registered-sha256 $(sha256sum $net | cut -d' ' -f1)); fi
  lab=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/v5/gates_v6.py accept --solve-dir $RUN/$rid "${reg[@]}" --repo . --out $RUN/$rid/V6_ACCEPTANCE.json 2> $RUN/$rid/v6.err | tail -1); log V6_$rid "$lab"
  env -u GRB_LICENSE_FILE "$PY" scripts_project/m10_batch3_summary.py stop-class --dir $RUN/$rid > $RUN/$rid/stop_class.log 2>&1; log STOPCLASS_$rid "$(tail -1 $RUN/$rid/stop_class.log)"
done
log DONE
