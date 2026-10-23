#!/bin/bash
# M10R B1.3: ONE local 56x3h Gurobi solve (authorised solve 1 of 3; user authorisation 2026-10-24: at most 3 local 56x3h solves, profile A,
# 30 min stop-loss each, no retry, >= 5 min between solves) of the keep-stock variant (cross_border.stock_mode=keep_stock_no_new) derived with
# scripts_project/m08a_variants.py from the M08b supplement-01 integrated 2920x3h base (results_project/m08b/builds_s01), truncated to the first
# 56 snapshots by s2_solve.py --truncate 56 (label SMOKE_TEST_ONLY), profile A formal_barrier, Gurobi TimeLimit 1,750 s, wall cap 1,800 s
# (process group killed). Post-processing with the v5 code (worktree HEAD efef93bf = package v5 e0a89f8e + report commits): violations, C1 with the
# smoke_s01 batch reference, M12 allocation (expected to fail with the ledger KeyError), Owen audit (skipped when ALLOCATION.json is missing),
# GATES_V6. The licence is only referenced through GRB_LICENSE_FILE for the solve (never read, never copied). No cloud, no upload.
set -u
WT=/home/jin/wt_m10p_20261022; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0
NETS=$MAIN/results_project/m08b/builds_s01; R=$MAIN/results_project/m10r; V=$R/variants; D=$R/keepstock_v5; ST=$R/STATUS.txt
REF=$MAIN/results_project/m08b/smoke_s01/BATCH_REFERENCE.json
LIC=/home/jin/gurobi.lic; TL=1750; WALL=1800; GAP=300; GRACE=60; N=56
AUTH="M10R B1.3 (user authorisation 2026-10-24 SGT: at most 3 local 56x3h Gurobi solves, profile A, 30 min stop-loss each, no retry, >= 5 min apart; no cloud, no upload, no 365x24h / 2920x3h solve): solve 1 of 3, keep-stock variant of the integrated 2920x3h base, first 56 snapshots, TimeLimit 1750 s"
mkdir -p $R $V $D; cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[g]urobi_cl' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
alive() { [ -n "$(pgrep -g "$1" 2>/dev/null)" ]; }
jget() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'): d=d.get(k) if isinstance(d, dict) else None
print(d)" "$1" "$2" 2>/dev/null; }
[ "$(git branch --show-current)" = codex/m10-batch3-20261022 ] || { log WRONG_BRANCH; exit 2; }
[ -f "$LIC" ] || { log NO_LICENCE_FILE; exit 3; }   # existence only
[ "$(busy)" = 0 ] || { log SOLVER_BUSY "$(busy) processes - not started"; exit 4; }
[ -f $D/SOLVE_RECEIPT.json ] && { log SKIP_EXISTING "no re-solve"; exit 0; }
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
log START "commit=$(git rev-parse HEAD):dirty=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l):profile=formal_barrier:truncate=$N:time_limit=$TL:wall_cap=$WALL"
# --- variant (deterministic; compared with the M08b s01 variant of the same base)
net=$V/disconnected_keepstock_2920_3h_unsolved.nc; rc=$V/disconnected_keepstock_2920_3h_VARIANT_RECEIPT.json
if [ ! -f $rc ]; then
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m08a_variants.py --repo . --base $NETS/integrated/integrated_2920_3h_unsolved.nc --out $V --set cross_border.stock_mode=keep_stock_no_new > $V/variant.log 2> $V/variant.err ); log VARIANT "exit=$?"
fi
sha=$(jget $rc output.sha256); act=$(sha256sum $net 2>/dev/null | cut -c1-64)
old=$(jget $MAIN/results_project/m08b/variants_s01/run1/keep_stock/disconnected_keepstock_2920_3h_VARIANT_RECEIPT.json output.sha256)
log VARIANT_SHA "receipt=$sha:file=$act:m08b_s01=$old:equal_m08b=$([ "$sha" = "$old" ] && echo yes || echo no)"
[ -n "$sha" ] && [ "$sha" = "$act" ] || { log VARIANT_SHA_MISMATCH "stop"; exit 5; }
# --- the solve (authorised solve 1 of 3)
if [ -f $R/.last_solve_end ]; then last=$(cat $R/.last_solve_end); while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done; log GAP "$(( $(date +%s) - last ))s"; fi
[ "$(busy)" = 0 ] || { log SOLVER_BUSY_SOLVE "$(busy) processes - stop"; exit 4; }
cmd=("$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario disconnected --output "$D" --label SMOKE_TEST_ONLY --authorization "$AUTH"
     --solver gurobi --solver-profile formal_barrier --scaling on --time-limit $TL --costs-table "$NETS/integrated/costs_active_research.csv" --truncate $N)
date +%s > $R/.solve1_start
( exec setsid env GRB_LICENSE_FILE=$LIC /usr/bin/time -v "${cmd[@]}" > $D/solve.log 2> $D/solve.err ) &
pid=$!; t0=$(date +%s); sleep 1; pg=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
log SOLVE_1 "pid=$pid:pgid=$pg:variant_sha256=$sha"
while kill -0 $pid 2>/dev/null; do
  sleep 5
  if [ $(( $(date +%s) - t0 )) -ge $WALL ]; then
    log KILLED_${WALL}S; kill -TERM -- "-$pg" 2>/dev/null; g=0
    while alive $pg && [ $g -lt $GRACE ]; do sleep 1; g=$((g + 1)); done
    alive $pg && { kill -KILL -- "-$pg" 2>/dev/null; log KILL9; }
    break
  fi
done
wait $pid 2>/dev/null; ex=$?; date +%s > $R/.last_solve_end; echo 1 > $R/.solves_used
log END_1 "exit=$ex:$(( $(date +%s) - t0 ))s:$(jget $D/SOLVE_RECEIPT.json termination_condition):$(jget $D/SOLVE_RECEIPT.json status):$(jget $D/SOLVE_RECEIPT.json objective):$(grep -h 'Maximum resident' $D/solve.err | awk '{printf "%.2fGiB", $NF/1048576}')"
log B16_V5 "passed=$(jget $D/V5_GATES.json B16_LEDGER.passed):error=$(jget $D/V5_GATES.json B16_LEDGER.error)"
# --- post-processing with the v5 code (licence variable removed)
if [ -f $D/solution/X.npy ]; then
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir $D --network "$net" --scenario disconnected --label SMOKE_TEST_ONLY \
      --out $D/VIOLATIONS.json --truncate $N > $D/c1_violations.log 2> $D/c1_violations.err ); log VIOLATIONS "exit=$?"
fi
( env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir $D --network "$net" --scenario disconnected --label SMOKE_TEST_ONLY \
    --violations $D/VIOLATIONS.json --reference $REF --truncate $N > $D/c1_precision.log 2> $D/c1_precision.err ); log C1 "exit=$?:grade=$(jget $D/PRECISION.json grade.grade):a=$(jget $D/PRECISION.json grade.a):b=$(jget $D/PRECISION.json grade.b):c=$(jget $D/PRECISION.json grade.c)"
if [ -f $D/SOLVE_RECEIPT.json ]; then
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir $D --scenario disconnected --label M10R_keepstock_v5 --out $D --register \
      > $D/m12.log 2> $D/m12.err ); log M12 "exit=$?:$(tail -1 $D/m12.err | cut -c1-120)"
  if [ -f $D/solution/X.npy ] && [ -f $D/ALLOCATION.json ]; then
    ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario disconnected --truncate $N --solve-dir $D \
        --allocation $D/ALLOCATION.json --tag M10R_keepstock_v5 --out $D/m12_owen --register-dir $D > $D/m12_owen.log 2> $D/m12_owen.err ); log M12_OWEN "exit=$?"
  else
    log M12_OWEN "skipped (no ALLOCATION.json)"
  fi
fi
lab=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/v5/gates_v6.py accept --solve-dir $D --registered-sha256 $sha --repo . --out $D/V6_ACCEPTANCE.json 2> $D/v6.err | tail -1)
log V6 "$lab"
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
log DONE
