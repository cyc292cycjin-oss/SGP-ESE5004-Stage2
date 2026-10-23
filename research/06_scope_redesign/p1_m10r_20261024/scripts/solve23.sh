#!/bin/bash
# M10R B3.3: the authorised local 56x3h Gurobi solves 2 and 3 (of at most 3; user authorisation 2026-10-24: profile A, 30 min stop-loss each,
# no retry, >= 5 min between solves): the two network types of the drill that have no real 56x3h result yet and matter most for the supplement -
#   solve 2: disconnected + finance.wacc_mode=country_specific (the R11 type; the run to be solved on the cloud),
#   solve 3: disconnected + disconnected.co2_shipping_intra_asean=forbid (the R8 / b1 type),
# both derived with m08a_variants.py from the M08b supplement-01 disconnected 2920x3h base, truncated to 56 snapshots by s2_solve.py --truncate 56,
# TimeLimit 1,750 s, wall cap 1,800 s (process group killed). Post-processing with the fixed code (worktree): violations, C1 (smoke_s01 batch
# reference), M12, Owen audit, GATES_V6. The licence is only referenced through GRB_LICENSE_FILE for the solves (never read, never copied).
set -u
WT=/home/jin/wt_m10p_20261022; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0
NETS=$MAIN/results_project/m08b/builds_s01; R=$MAIN/results_project/m10r; V=$R/variants; ST=$R/STATUS.txt
REF=$MAIN/results_project/m08b/smoke_s01/BATCH_REFERENCE.json
LIC=/home/jin/gurobi.lic; TL=1750; WALL=1800; GAP=300; GRACE=60; N=56
AUTH="M10R B3.3 (user authorisation 2026-10-24 SGT: at most 3 local 56x3h Gurobi solves, profile A, 30 min stop-loss each, no retry, >= 5 min apart; no cloud, no upload, no 365x24h / 2920x3h solve)"
cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[g]urobi_cl' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
alive() { [ -n "$(pgrep -g "$1" 2>/dev/null)" ]; }
jget() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'): d=d.get(k) if isinstance(d, dict) else None
print(d)" "$1" "$2" 2>/dev/null; }
[ "$(git branch --show-current)" = codex/m10-batch3-20261022 ] || { log WRONG_BRANCH; exit 2; }
[ -f "$LIC" ] || { log NO_LICENCE_FILE; exit 3; }   # existence only
[ "$(busy)" = 0 ] || { log SOLVER_BUSY "$(busy) processes - not started"; exit 4; }
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
used=$(cat $R/.solves_used 2>/dev/null || echo 0)
run_one() {   # $1 solve number $2 tag $3 --set value $4 extra args (costs)
  local k=$1 tag=$2 set=$3 extra=${4:-}
  local D=$R/$tag; mkdir -p $D
  [ -f $D/SOLVE_RECEIPT.json ] && { log SKIP_EXISTING_$tag "no re-solve"; return 0; }
  [ "$used" -lt 3 ] || { log REFUSED_$tag "3 solves already used"; return 1; }
  local net rc
  if [ ! -f "$V/${tag}_2920_3h_unsolved.nc" ]; then
    mkdir -p $V/gen_$tag
    ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m08a_variants.py --repo . --base $NETS/disconnected/disconnected_2920_3h_unsolved.nc --out $V/gen_$tag --set "$set" $extra > $V/gen_$tag.log 2>&1 ); log VARIANT_$tag "exit=$?"
  fi
  net=$(ls $V/gen_$tag/*_unsolved.nc | head -1); rc=$(ls $V/gen_$tag/*_VARIANT_RECEIPT.json | head -1)
  local sha=$(jget $rc output.sha256); local act=$(sha256sum $net | cut -c1-64)
  log VARIANT_SHA_$tag "receipt=$sha:file=$act"; [ -n "$sha" ] && [ "$sha" = "$act" ] || { log VARIANT_SHA_MISMATCH_$tag stop; return 1; }
  if [ -f $R/.last_solve_end ]; then local last=$(cat $R/.last_solve_end); while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done; log GAP_$tag "$(( $(date +%s) - last ))s"; fi
  [ "$(busy)" = 0 ] || { log SOLVER_BUSY_$tag "$(busy) processes - stop"; return 1; }
  local cmd=("$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario disconnected --output "$D" --label SMOKE_TEST_ONLY --authorization "$AUTH: solve $k of 3, $tag, first 56 snapshots, TimeLimit 1750 s"
       --solver gurobi --solver-profile formal_barrier --scaling on --time-limit $TL --costs-table "$NETS/disconnected/costs_active_research.csv" --truncate $N)
  date +%s > $R/.solve${k}_start
  ( exec setsid env GRB_LICENSE_FILE=$LIC /usr/bin/time -v "${cmd[@]}" > $D/solve.log 2> $D/solve.err ) &
  local pid=$! t0=$(date +%s); sleep 1; local pg=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  log SOLVE_$k "tag=$tag:pid=$pid:pgid=$pg:variant_sha256=$sha"
  while kill -0 $pid 2>/dev/null; do
    sleep 5
    if [ $(( $(date +%s) - t0 )) -ge $WALL ]; then
      log KILLED_${WALL}S_$tag; kill -TERM -- "-$pg" 2>/dev/null; local g=0
      while alive $pg && [ $g -lt $GRACE ]; do sleep 1; g=$((g + 1)); done
      alive $pg && { kill -KILL -- "-$pg" 2>/dev/null; log KILL9_$tag; }
      break
    fi
  done
  wait $pid 2>/dev/null; local ex=$?; date +%s > $R/.last_solve_end; used=$((used + 1)); echo $used > $R/.solves_used
  log END_$k "tag=$tag:exit=$ex:$(( $(date +%s) - t0 ))s:$(jget $D/SOLVE_RECEIPT.json termination_condition):$(jget $D/SOLVE_RECEIPT.json status):$(jget $D/SOLVE_RECEIPT.json objective):$(grep -h 'Maximum resident' $D/solve.err | awk '{printf "%.2fGiB", $NF/1048576}')"
  log B16_$tag "passed=$(jget $D/V5_GATES.json B16_LEDGER.passed):rel=$(jget $D/V5_GATES.json B16_LEDGER.relative_error)"
  if [ -f $D/solution/X.npy ]; then
    ( env -u GRB_LICENSE_FILE "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir $D --network "$net" --scenario disconnected --label SMOKE_TEST_ONLY \
        --out $D/VIOLATIONS.json --truncate $N > $D/c1_violations.log 2> $D/c1_violations.err ); log VIOLATIONS_$tag "exit=$?"
  fi
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir $D --network "$net" --scenario disconnected --label SMOKE_TEST_ONLY \
      --violations $D/VIOLATIONS.json --reference $REF --truncate $N > $D/c1_precision.log 2> $D/c1_precision.err ); log C1_$tag "exit=$?:grade=$(jget $D/PRECISION.json grade.grade):a=$(jget $D/PRECISION.json grade.a):b=$(jget $D/PRECISION.json grade.b):c=$(jget $D/PRECISION.json grade.c)"
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir $D --scenario disconnected --label M10R_$tag --out $D --register > $D/m12.log 2> $D/m12.err ); log M12_$tag "exit=$?"
  if [ -f $D/solution/X.npy ] && [ -f $D/ALLOCATION.json ]; then
    ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario disconnected --truncate $N --solve-dir $D \
        --allocation $D/ALLOCATION.json --tag M10R_$tag --out $D/m12_owen --register-dir $D > $D/m12_owen.log 2> $D/m12_owen.err ); log M12_OWEN_$tag "exit=$?"
  fi
  local lab=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/v5/gates_v6.py accept --solve-dir $D --registered-sha256 $sha --repo . --out $D/V6_ACCEPTANCE.json 2> $D/v6.err | tail -1)
  log V6_$tag "$lab"
  return 0
}
run_one 2 wacc_disconnected "finance.wacc_mode=country_specific" "--costs $NETS/disconnected/costs_active_research.csv"
run_one 3 b1_disconnected "disconnected.co2_shipping_intra_asean=forbid" ""
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
log DONE_23
