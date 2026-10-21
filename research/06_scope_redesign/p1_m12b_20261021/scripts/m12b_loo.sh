#!/bin/bash
# M12b section 2.2: the 11 leave-one-out solves on the local machine (Gurobi; needs the user's authorisation in the session, recorded in AUTH).
# Variants results_project/m12b/variants/integrated_minus<CC>_2920_3h_unsolved.nc (m08a_variants.py from builds_s01 integrated 2920x3h, bca20fc0...),
# s2_solve.py --truncate 56 (label SMOKE_TEST_ONLY), profile A formal_barrier, Gurobi TimeLimit 1,750 s, wall cap 1,800 s (process group killed),
# serial, >= 330 s between the end of one solve and the start of the next (first gap from the M08b smoke_s01 end), no retry, no parameter change;
# a run that does not reach the usable standard is recorded and the next one follows. After each solve (licence variable removed): violations,
# C1 (s4o_c1_precision run with the batch reference of smoke_s01 = the integrated / disconnected pair of the same network, profile and truncation),
# M12 allocation + Owen dual form (registered in EXPORTS.json), right-hand-side check against the full run, GATES_V6 acceptance (G2.1 against the
# variant receipt's output.sha256). The licence is only referenced through GRB_LICENSE_FILE for the solve (never read, never copied).
# After the 11 runs: m12_allocation.py loo (c'(i), check against the Owen dual form and the market form, SCRB with all 11).
set -u
WT=/home/jin/wt_m12_20261021; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0
NETS=$MAIN/results_project/m08b/builds_s01; SMOKE=$MAIN/results_project/m08b/smoke_s01; M=$MAIN/results_project/m12b
V=$M/variants; ST=$M/STATUS.txt; REF=$SMOKE/BATCH_REFERENCE.json; FULL=$M/full_integrated; DIS=$M/full_disconnected
LIC=/home/jin/gurobi.lic; TL=1750; WALL=1800; GAP=330; GRACE=60; N=56
COUNTRIES=${COUNTRIES:-"BN ID KH LA MM MY PH SG TH TL VN"}
AUTH="PENDING"
case "$AUTH" in PENDING*) echo "no user authorisation recorded in AUTH - not started"; exit 5;; esac
cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
busy() { ps -eo cmd | grep -cE '[s]2_solve.py|[g]urobi_cl'; }
alive() { [ -n "$(pgrep -g "$1" 2>/dev/null)" ]; }
jget() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'): d=d.get(k) if isinstance(d, dict) else None
print(d)" "$1" "$2" 2>/dev/null; }
[ "$(git branch --show-current)" = codex/m12b-loo-local-20261021 ] || { log WRONG_BRANCH; exit 2; }
[ -f "$LIC" ] || { log NO_LICENCE_FILE; exit 3; }   # existence only
[ "$(busy)" = 0 ] || { log SOLVER_BUSY "$(busy) processes - not started"; exit 4; }
[ -f $FULL/m12_owen/RHS_BY_FAMILY_OWNER.csv ] || { log NO_FULL_AUDIT "run m12b_prep.sh STEP=full first"; exit 6; }
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
[ -f $M/.last_solve_end ] || cp -p $SMOKE/.last_solve_end $M/.last_solve_end
log START "commit=$(git rev-parse HEAD):dirty=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l):profile=formal_barrier:truncate=$N:time_limit=$TL:wall_cap=$WALL:gap=$GAP:countries=$COUNTRIES"
for c in $COUNTRIES; do
  tag=integrated_minus$c; dir=$M/$tag; net=$V/${tag}_2920_3h_unsolved.nc; rc=$V/${tag}_2920_3h_VARIANT_RECEIPT.json; mkdir -p $dir
  if [ -f $dir/SOLVE_RECEIPT.json ]; then log SKIP_EXISTING_$c "no re-solve"; continue; fi
  sha=$(jget $rc output.sha256); act=$(sha256sum $net 2>/dev/null | cut -c1-64)
  if [ -z "$sha" ] || [ "$sha" != "$act" ]; then log VARIANT_SHA_MISMATCH_$c "receipt=${sha:-missing}:file=${act:-missing}:skipped"; continue; fi
  last=$(cat $M/.last_solve_end); while [ $(( $(date +%s) - last )) -lt $GAP ]; do sleep 5; done; log GAP_$c "$(( $(date +%s) - last ))s"
  [ "$(busy)" = 0 ] || { log SOLVER_BUSY_$c "$(busy) processes - stop"; break; }
  cmd=("$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario integrated --output "$dir" --label SMOKE_TEST_ONLY --authorization "$AUTH; run minus$c"
       --solver gurobi --solver-profile formal_barrier --scaling on --time-limit $TL --costs-table "$NETS/integrated/costs_active_research.csv" --truncate $N)
  ( exec setsid env GRB_LICENSE_FILE=$LIC /usr/bin/time -v "${cmd[@]}" > $dir/solve.log 2> $dir/solve.err ) &
  pid=$!; t0=$(date +%s); sleep 1; pg=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
  log SOLVE_$c "pid=$pid:pgid=$pg:variant_sha256=$sha"
  while kill -0 $pid 2>/dev/null; do
    sleep 5
    if [ $(( $(date +%s) - t0 )) -ge $WALL ]; then
      log KILLED_${WALL}S_$c; kill -TERM -- "-$pg" 2>/dev/null; g=0
      while alive $pg && [ $g -lt $GRACE ]; do sleep 1; g=$((g + 1)); done
      alive $pg && { kill -KILL -- "-$pg" 2>/dev/null; log KILL9_$c; }
      break
    fi
  done
  wait $pid 2>/dev/null; ex=$?; date +%s > $M/.last_solve_end
  log END_$c "exit=$ex:$(( $(date +%s) - t0 ))s:$(jget $dir/SOLVE_RECEIPT.json termination_condition):$(jget $dir/SOLVE_RECEIPT.json status):$(jget $dir/SOLVE_RECEIPT.json objective):$(grep -h 'Maximum resident' $dir/solve.err | awk '{printf "%.2fGiB", $NF/1048576}')"
  if [ -f $dir/solution/X.npy ]; then
    ( env -u GRB_LICENSE_FILE "$PY" scripts_project/l23_violation_analysis.py --repo . --solve-dir $dir --network "$net" --scenario integrated --label SMOKE_TEST_ONLY \
        --out $dir/VIOLATIONS.json --truncate $N > $dir/c1_violations.log 2> $dir/c1_violations.err ); log VIOLATIONS_$c "exit=$?"
  fi
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/s4o_c1_precision.py run --repo . --solve-dir $dir --network "$net" --scenario integrated --label SMOKE_TEST_ONLY \
      --violations $dir/VIOLATIONS.json --reference $REF --truncate $N > $dir/c1_precision.log 2> $dir/c1_precision.err ); log C1_$c "exit=$?:grade=$(jget $dir/PRECISION.json grade.grade):a=$(jget $dir/PRECISION.json grade.a):b=$(jget $dir/PRECISION.json grade.b):c=$(jget $dir/PRECISION.json grade.c)"
  if [ -f $dir/SOLVE_RECEIPT.json ]; then
    ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py run --repo . --solve-dir $dir --scenario integrated --label M12B_$tag --out $dir --register \
        > $dir/m12.log 2> $dir/m12.err ); log M12_$c "exit=$?"
    if [ -f $dir/solution/X.npy ] && [ -f $dir/ALLOCATION.json ]; then
      ( env -u GRB_LICENSE_FILE /usr/bin/time -v "$PY" scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario integrated --truncate $N --solve-dir $dir \
          --allocation $dir/ALLOCATION.json --tag M12B_$tag --out $dir/m12_owen --register-dir $dir > $dir/m12_owen.log 2> $dir/m12_owen.err ); log M12_OWEN_$c "exit=$?"
      ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_rhs_audit.py loo --full $FULL/m12_owen/RHS_BY_FAMILY_OWNER.csv --variant $dir/m12_owen/RHS_BY_FAMILY_OWNER.csv \
          --removed $c --out $dir/m12_loo_rhs > $dir/m12_loo_rhs.log 2>&1 ); log RHS_CHECK_$c "exit=$?:$(tail -1 $dir/m12_loo_rhs.log)"
    fi
  fi
  lab=$(env -u GRB_LICENSE_FILE "$PY" scripts_project/v5/gates_v6.py accept --solve-dir $dir --registered-sha256 $sha --repo . --out $dir/V6_ACCEPTANCE.json 2> $dir/v6.err | tail -1)
  log V6_$c "$lab"
done
args=(); for c in $COUNTRIES; do [ -f $M/integrated_minus$c/SOLVE_RECEIPT.json ] && args+=(--loo "$c=$M/integrated_minus$c"); done
if [ ${#args[@]} -gt 0 ]; then
  ( env -u GRB_LICENSE_FILE "$PY" scripts_project/m12_allocation.py loo --full $FULL "${args[@]}" --standalone $DIS --out $M/LOO_CHECK > $M/LOO_CHECK.log 2>&1 )
  log M12_LOO "exit=$?:runs=$(( ${#args[@]} / 2 )):$(tail -1 $M/LOO_CHECK.log)"
fi
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
log DONE
