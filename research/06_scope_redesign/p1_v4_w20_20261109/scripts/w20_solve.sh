#!/bin/bash
# V4 W20 section 4 (V4_W20_INSTRUCTION.md SHA f4419a83): at most 17 local 56-snapshot solves of the coalition networks, authorised by the instruction itself
# ("用户启动本指令即授权"), in the order GMS, LTMS, BIMP, the three complements, the 11 leave-one-out coalitions. Same path and settings as the D2c / W14
# smoke (smoke_d2c.sh): profile formal_barrier_1e6_t16, --truncate 56 (the networks are already cut by the same rule; LP identity checked, logs/lpcheck.txt),
# --scaling on, Gurobi TimeLimit 3,000 s, wall cap 3,600 s (process group killed), label SMOKE_TEST_ONLY; serial, >= 330 s apart, at most one Gurobi process;
# a bare TCP connect to the token server before every solve (no data, no licence). No retry, no parameter change. A non-optimal run is recorded and the
# batch continues (instruction section 4); a core-condition violation beyond the registered threshold stops the batch (section 0 / 6).
# Licence only through GRB_LICENSE_FILE for the solve (never read, never copied); raw solve.log / solve.err stay in results_project (scrubbed copies for evidence).
set -u
WT=/home/jin/wt_v4_w20; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w20_20261109
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
NETS=$MAIN/results_project/v4w20/nets56; COSTS=$MAIN/results_project/v4w14/builds/main/integrated/costs_active_research.csv
RUN=$MAIN/results_project/v4w20/solves; ST=$RUN/STATUS.txt; XS=$W/evidence/W20_XS_PRE.json; VLOG=$W/evidence/W20_RUN_VERDICTS.jsonl
LIC=/home/jin/gurobi.lic; TL=3000; WALL=3600; GAP=330; GRACE=60; N=56; PROFILE=formal_barrier_1e6_t16; MAXSOLVES=17
[ "${1:-}" = "--confirmed" ] || { echo "REFUSED: needs --confirmed <time>"; exit 5; }
AUTH="V4 W20 section 4 (V4_W20_INSTRUCTION.md SHA f4419a83, at most 17 local 56-snapshot coalition solves authorised by starting the instruction; ${2:?time}): profile $PROFILE, TimeLimit $TL s, wall cap $WALL s, no retry"
mkdir -p $RUN; cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[g]urobi_cl|[b]4_split_solve\.py|[s]2_network\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
alive() { [ -n "$(pgrep -g "$1" 2>/dev/null)" ]; }
token_route() { timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null; }
[ -f "$LIC" ] || { log NO_LICENCE_FILE; exit 3; }
[ -f "$XS" ] || { log NO_REGISTERED_XS; exit 3; }
git -C $WT log --format=%H -- research/06_scope_redesign/p1_v4_w20_20261109/CORE_CHECK_V4_56.md | grep -q . || { log NOT_REGISTERED "CORE_CHECK_V4_56.md section 1 not committed - not started"; exit 2; }
token_route || { log NO_TOKEN_ROUTE "token server not reachable from WSL (AnyConnect?) - not started"; exit 6; }
[ "$(busy)" = 0 ] || { log SOLVER_BUSY "$(busy) processes - not started"; exit 4; }
[ "$(ps -eo args= | grep -c '[p]ytest')" = 0 ] || { log PYTEST_RUNNING "not started"; exit 4; }
D=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l); [ "$D" = 0 ] || { log DIRTY "$D tracked changes - not started"; exit 2; }
ORDER=$($PY scripts_project/v4_coalition.py list | cut -d' ' -f1)
log START "commit=$(git rev-parse HEAD):profile=$PROFILE:truncate=$N:time_limit=$TL:wall_cap=$WALL:order=$(echo $ORDER | tr ' ' ',')"
calls=$(ls $RUN/*/SOLVE_RECEIPT.json 2>/dev/null | wc -l)
for rid in $ORDER; do
  dir=$RUN/$rid; net=$NETS/${rid}_56_unsolved.nc; mkdir -p $dir
  if [ -f $dir/SOLVE_RECEIPT.json ]; then log SKIP_EXISTING_$rid "no re-solve"; continue; fi
  [ "$calls" -lt "$MAXSOLVES" ] || { log STOP_QUOTA "$calls solver calls"; break; }
  if [ -f $RUN/.last_solve_end ]; then
    last=$(cat $RUN/.last_solve_end); while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done; log GAP_$rid "$(( $(date +%s) - last ))s"
  fi
  [ "$(busy)" = 0 ] || { log SOLVER_BUSY_$rid "$(busy) processes - stop"; break; }
  token_route || { log NO_TOKEN_ROUTE_$rid "token server not reachable from WSL - stop"; break; }
  want=$($PY -c "import json,sys; print(json.load(open(sys.argv[1]))['coalitions'][sys.argv[2]]['network_sha256'])" $XS $rid); have=$(sha256sum $net | cut -c1-64)
  [ "$want" = "$have" ] || { log NETWORK_DIFFERS_$rid "$have != registered $want - stop"; break; }
  log NETWORK_$rid "$have"
  cmd=("$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario integrated --output "$dir" --label SMOKE_TEST_ONLY --authorization "$AUTH; run $rid"
       --solver gurobi --solver-profile $PROFILE --scaling on --time-limit $TL --costs-table "$COSTS" --truncate $N)
  ( exec setsid env GRB_LICENSE_FILE=$LIC /usr/bin/time -v "${cmd[@]}" > $dir/solve.log 2> $dir/solve.err ) &
  pid=$!; t0=$(date +%s); calls=$((calls + 1)); sleep 1; pg=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  log SOLVE_$rid "pid=$pid:pgid=$pg:call=$calls"
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
  if [ -f $dir/solution/X.npy ]; then
    ( env -u GRB_LICENSE_FILE "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir $dir --network "$net" --scenario integrated --label SMOKE_TEST_ONLY --out $dir/VIOLATIONS.json --truncate $N > $dir/c1_violations.log 2>&1 ); log VIOLATIONS_$rid "exit=$?"
    ( env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir $dir --network "$net" --scenario integrated --label SMOKE_TEST_ONLY --violations $dir/VIOLATIONS.json --truncate $N > $dir/c1_precision.log 2>&1 ); log C1_$rid "exit=$?"
  fi
  v=$(env -u GRB_LICENSE_FILE "$PY" $W/scripts/w20_eval.py --run-dir $dir --name $rid --xs $XS --log $VLOG); ev=$?; log EVAL_$rid "$v"
  if [ $ev = 3 ]; then log STOP_VIOLATION_$rid "core condition violated beyond the registered threshold - the remaining runs are not started (instruction sections 0 and 6)"; break; fi
done
log DONE "calls=$calls"
