#!/bin/bash
# V4 W20b section 4 (V4_W20B_INSTRUCTION.md SHA 25f1db61; decision 230): at most 18 local 56-snapshot solves, authorised by the instruction itself
# ("用户启动本指令即授权"), in the order R0, the three blocs, the three complements, the 11 leave-one-out coalitions (v4_coalition.py list --w20b).
# Same path and settings as W20 / the D2c-W14 smoke: profile formal_barrier_1e6_t16, --truncate 56 (networks already cut by the same rule), --scaling on,
# Gurobi TimeLimit 3,000 s, wall cap 3,600 s (process group killed), label SMOKE_TEST_ONLY; serial, >= 330 s apart, at most one Gurobi process; a bare
# TCP connect to the token server before every solve (no data, no licence). No retry, no parameter change. A non-optimal run is recorded and the batch
# continues (section 4); a violation beyond the registered threshold stops the batch (sections 4 / 5).
# After each run's analyses (violations, C1, verdict) the large arrays lp/*.npy, solution/*.npy, v5/kkt/*/*.npy are compressed losslessly with gzip -1 -n
# (manifest of the original SHA256 and sizes written first, every .gz checked by decompression against it; gunzip restores the files): disk budget 5 GB
# (section 5). The batch stops before a solve when results_project/v4w20b exceeds 4.0 GB.
# Licence only through GRB_LICENSE_FILE for the solve (never read, never copied); raw solve.log / solve.err stay in results_project (scrubbed copies for evidence).
set -u
WT=/home/jin/wt_v4_w20b; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w20b_20261109
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
NETS=$MAIN/results_project/v4w20b/nets56; COSTS=$MAIN/results_project/v4w14/builds/main/integrated/costs_active_research.csv
RES=$MAIN/results_project/v4w20b; RUN=$RES/solves; ST=$RUN/STATUS.txt; XS=$W/evidence/W20B_XS_PRE.json; VLOG=$W/evidence/W20B_RUN_VERDICTS.jsonl
LIC=/home/jin/gurobi.lic; TL=3000; WALL=3600; GAP=330; GRACE=60; N=56; PROFILE=formal_barrier_1e6_t16; MAXSOLVES=18; DISKMAX=4000000000
[ "${1:-}" = "--confirmed" ] || { echo "REFUSED: needs --confirmed <time>"; exit 5; }
AUTH="V4 W20b section 4 (V4_W20B_INSTRUCTION.md SHA 25f1db61, at most 18 local 56-snapshot solves authorised by starting the instruction; ${2:?time}): profile $PROFILE, TimeLimit $TL s, wall cap $WALL s, no retry"
mkdir -p $RUN; cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[g]urobi_cl|[b]4_split_solve\.py|[s]2_network\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
alive() { [ -n "$(pgrep -g "$1" 2>/dev/null)" ]; }
token_route() { timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null; }
. $W/scripts/w20b_pack.sh || { echo "pack helper missing"; exit 3; }   # pack <run dir>: lossless gzip of the large arrays (see header)
[ -f "$LIC" ] || { log NO_LICENCE_FILE; exit 3; }
[ -f "$XS" ] || { log NO_REGISTERED_XS; exit 3; }
git -C $WT log --format=%H -- research/06_scope_redesign/p1_v4_w20b_20261109/CORE_CHECK_V4_56_BUNKER.md | grep -q . || { log NOT_REGISTERED "CORE_CHECK_V4_56_BUNKER.md section 1 not committed - not started"; exit 2; }
git -C $WT log --format=%H -- research/06_scope_redesign/p1_v4_w20b_20261109/evidence/W20B_XS_PRE.json | grep -q . || { log NOT_REGISTERED "W20B_XS_PRE.json not committed - not started"; exit 2; }
token_route || { log NO_TOKEN_ROUTE "token server not reachable from WSL (AnyConnect?) - not started"; exit 6; }
[ "$(busy)" = 0 ] || { log SOLVER_BUSY "$(busy) processes - not started"; exit 4; }
[ "$(ps -eo args= | grep -c '[p]ytest')" = 0 ] || { log PYTEST_RUNNING "not started"; exit 4; }
D=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l); [ "$D" = 0 ] || { log DIRTY "$D tracked changes - not started"; exit 2; }
LIST=$($PY scripts_project/v4_coalition.py list --w20b); ORDER=$(echo "$LIST" | cut -d' ' -f1)
log START "commit=$(git rev-parse HEAD):profile=$PROFILE:truncate=$N:time_limit=$TL:wall_cap=$WALL:order=$(echo $ORDER | tr ' ' ',')"
calls=$(ls $RUN/*/SOLVE_RECEIPT.json 2>/dev/null | wc -l)
for rid in $ORDER; do
  netname=$(echo "$LIST" | awk -v r="$rid" '$1==r {print $2}')
  dir=$RUN/$rid; net=$NETS/${netname}_56_unsolved.nc; mkdir -p $dir
  if [ -f $dir/SOLVE_RECEIPT.json ]; then log SKIP_EXISTING_$rid "no re-solve"; continue; fi
  [ "$calls" -lt "$MAXSOLVES" ] || { log STOP_QUOTA "$calls solver calls"; break; }
  used=$(du -sb $RES | cut -f1); [ "$used" -lt "$DISKMAX" ] || { log STOP_DISK_BUDGET_$rid "$used bytes in results_project/v4w20b"; break; }
  if [ -f $RUN/.last_solve_end ]; then
    last=$(cat $RUN/.last_solve_end); while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done; log GAP_$rid "$(( $(date +%s) - last ))s"
  fi
  [ "$(busy)" = 0 ] || { log SOLVER_BUSY_$rid "$(busy) processes - stop"; break; }
  token_route || { log NO_TOKEN_ROUTE_$rid "token server not reachable from WSL - stop"; break; }
  want=$($PY -c "import json,sys; print(json.load(open(sys.argv[1]))['runs'][sys.argv[2]]['network_sha256'])" $XS $rid); have=$(sha256sum $net | cut -c1-64)
  [ "$want" = "$have" ] || { log NETWORK_DIFFERS_$rid "$have != registered $want - stop"; break; }
  log NETWORK_$rid "$netname:$have"
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
  v=$(env -u GRB_LICENSE_FILE "$PY" $W/scripts/w20b_eval.py --run-dir $dir --name $rid --xs $XS --log $VLOG); ev=$?; log EVAL_$rid "$v"
  log PACK_$rid "$(pack $dir)"
  if [ $ev = 3 ]; then log STOP_VIOLATION_$rid "condition violated beyond the registered threshold - the remaining runs are not started (instruction sections 4 and 5)"; break; fi
done
log DONE "calls=$calls"
