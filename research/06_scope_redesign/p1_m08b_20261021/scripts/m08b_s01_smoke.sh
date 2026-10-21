#!/bin/bash
# M08b supplement 01 section 4.3 (user authorisation 2026-10-21, cloud idle confirmed by the user): local smoke on the supplement-01 2920x3h
# networks (results_project/m08b/builds_s01) truncated to the first 56 snapshots (s2_solve.py --truncate 56, label SMOKE_TEST_ONLY), integrated
# and disconnected once each, profile A (formal_barrier), Gurobi TimeLimit 1,750 s, wall cap 1,800 s per run (30 min stop-loss, process group
# killed), serial with >= 330 s between solves. No retry, no parameter change. Same steps as the first round (scripts/m08b_smoke.sh) except:
# networks builds_s01, output smoke_s01, GATES_V6 via --build-receipt (corrected SHA choice, supplement 01 item D) instead of --registered-sha256.
# The licence is only referenced through GRB_LICENSE_FILE for the solve (never read, never copied); violations / C1 / GATES_V6 run without it.
set -u
WT=/home/jin/wt_m08b_20261021; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
NETS=$MAIN/results_project/m08b/builds_s01; RUN=$MAIN/results_project/m08b/smoke_s01; ST=$RUN/STATUS.txt
LIC=/home/jin/gurobi.lic; TL=1750; WALL=1800; GAP=330; GRACE=60; N=56
AUTH="M08b supplement 01 section 4.3 (user authorisation 2026-10-21, cloud idle confirmed): local 56x3h smoke on builds_s01, integrated + disconnected once each, profile A formal_barrier, TimeLimit 1750 s, stop-loss 30 min, no retry"
mkdir -p $RUN; cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
busy() { ps -eo cmd | grep -cE '[s]2_solve.py|[g]urobi_cl'; }
alive() { [ -n "$(pgrep -g "$1" 2>/dev/null)" ]; }
[ -f "$LIC" ] || { log NO_LICENCE_FILE; exit 3; }   # existence only
[ "$(busy)" = 0 ] || { log SOLVER_BUSY "$(busy) processes - not started"; exit 4; }
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
log START "commit=$(git rev-parse HEAD):dirty=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l):profile=formal_barrier:truncate=$N:time_limit=$TL:wall_cap=$WALL:networks=builds_s01"
for sc in integrated disconnected; do
  dir=$RUN/$sc; net=$NETS/$sc/${sc}_2920_3h_unsolved.nc; mkdir -p $dir
  if [ -f $dir/SOLVE_RECEIPT.json ]; then log SKIP_EXISTING_$sc "no re-solve"; continue; fi
  if [ -f $RUN/.last_solve_end ]; then
    last=$(cat $RUN/.last_solve_end); while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done; log GAP_$sc "$(( $(date +%s) - last ))s"
  fi
  [ "$(busy)" = 0 ] || { log SOLVER_BUSY_$sc "$(busy) processes - stop"; break; }
  cmd=("$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario $sc --output "$dir" --label SMOKE_TEST_ONLY --authorization "$AUTH; run $sc"
       --solver gurobi --solver-profile formal_barrier --scaling on --time-limit $TL --costs-table "$NETS/$sc/costs_active_research.csv" --truncate $N)
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
done
if [ -f $RUN/integrated/COUNTRY_COST_LEDGER.csv ] && [ -f $RUN/disconnected/COUNTRY_COST_LEDGER.csv ]; then
  env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py reference --integrated $RUN/integrated --disconnected $RUN/disconnected --out $RUN/BATCH_REFERENCE.json > $RUN/c1_reference.log 2>&1
  log BATCH_REFERENCE "exit=$?"
  for sc in integrated disconnected; do
    env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py regrade --solve-dir $RUN/$sc --reference $RUN/BATCH_REFERENCE.json > $RUN/$sc/c1_regrade.log 2>&1; log REGRADE_$sc "exit=$?"
  done
else
  log BATCH_REFERENCE "missing ledgers"
fi
for sc in integrated disconnected; do
  # supplement 01 item D: the registered SHA comes from the build receipt through the corrected rule (truncated run -> the 2920x3h network)
  br=$NETS/$sc/${sc}_BUILD_RECEIPT.json
  lab=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/v5/gates_v6.py accept --solve-dir $RUN/$sc --build-receipt $br --repo . --out $RUN/$sc/V6_ACCEPTANCE.json 2> $RUN/$sc/v6.err | tail -1)
  chk=$("$PY" -c "import json,sys; a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); g=a['G2']['G2_1']; print('registered=' + str(g['registered_sha256'])[:16] + ':equals_2920x3h=' + str(g['registered_sha256'] == b['network']['sha256']))" $RUN/$sc/V6_ACCEPTANCE.json $br 2>/dev/null || echo "registered=?")
  log V6_$sc "$lab:$chk"
done
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
log DONE
