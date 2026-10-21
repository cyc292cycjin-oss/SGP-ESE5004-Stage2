#!/bin/bash
# M12b section 2.1 (no solve, no Gurobi): STEP=full | variants | loops
#   full     : reuse the M08b supplement-01 second-smoke runs (results_project/m08b/smoke_s01/{integrated,disconnected}: builds_s01 2920x3h,
#              first 56 snapshots, profile A formal_barrier, exported lp/ + solution/). New dirs results_project/m12b/full_<sc>/ hold SYMLINKS to
#              the run files (read only; EXPORTS.json is not linked and nothing is registered, so the M08b smoke dir is never written) plus the
#              M12 outputs: ALLOCATION.* (m12_allocation.py run) and m12_owen/ (m12_rhs_audit.py audit, Owen dual form, item-138 acceptance).
#   variants : the 11 leave-one-out variants from the SAME base network (builds_s01 integrated 2920x3h, bca20fc0...) with m08a_variants.py
#              --set coalition.remove_countries=[CC] (no --allow-stale-base), receipts + SHA256 -> results_project/m12b/variants/
#   loops    : KVL loop counts (m12b_loops.py) of the full network and the 11 variants
set -u
WT=/home/jin/wt_m12_20261021; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0
NETS=$MAIN/results_project/m08b/builds_s01; SMOKE=$MAIN/results_project/m08b/smoke_s01; M=$MAIN/results_project/m12b
SCR=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12b_20261021/scripts; EV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12b_20261021/evidence
BASE=$NETS/integrated/integrated_2920_3h_unsolved.nc; BASE_SHA=bca20fc08a149772074b620e1f587e86b0306c29e81d138fa67f4a9b9ae53cab
COUNTRIES="BN ID KH LA MM MY PH SG TH TL VN"
mkdir -p $M $EV; ST=$M/PREP_STATUS.txt; cd $WT || exit 1
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" | tee -a $ST; }
[ "$(git branch --show-current)" = codex/m12b-loo-local-20261021 ] || { log WRONG_BRANCH; exit 2; }
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
case "${STEP:?}" in
  full)
    for sc in integrated disconnected; do
      src=$SMOKE/$sc; dst=$M/full_$sc; net=$NETS/$sc/${sc}_2920_3h_unsolved.nc; mkdir -p $dst
      for f in SOLVE_RECEIPT.json PRECISION.json V6_ACCEPTANCE.json VIOLATIONS.json COUNTRY_COST_LEDGER.csv ${sc}_SMOKE_TEST_ONLY_solved.nc lp solution; do
        [ -e $dst/$f ] || ln -s $src/$f $dst/$f
      done
      log REUSE_$sc "commit_of_run=$(grep -o 'commit=[0-9a-f]*' $SMOKE/STATUS.txt | head -1):head=$(git rev-parse --short HEAD)"
      ( /usr/bin/time -v $PY scripts_project/m12_allocation.py run --repo . --solve-dir $dst --scenario $sc --label M12B_REUSE_SMOKE_S01_$sc --out $dst \
          > $dst/m12.log 2> $dst/m12.err ); log M12_RUN_$sc "exit=$?"
      ( /usr/bin/time -v $PY scripts_project/m12_rhs_audit.py audit --repo . --network $net --scenario $sc --truncate 56 --solve-dir $dst \
          --allocation $dst/ALLOCATION.json --tag M12B_FULL_$sc --out $dst/m12_owen > $dst/m12_owen.log 2> $dst/m12_owen.err ); log M12_OWEN_$sc "exit=$?:$(grep -h 'Maximum resident' $dst/m12_owen.err | awk '{printf "%.2fGiB", $NF/1048576}')"
    done ;;
  variants)
    act=$(sha256sum $BASE | cut -c1-64); [ "$act" = "$BASE_SHA" ] || { log BASE_SHA_MISMATCH "$act"; exit 3; }
    log BASE "sha256=$act"
    mkdir -p $M/variants $EV/variant_receipts
    for c in $COUNTRIES; do
      ( /usr/bin/time -v $PY scripts_project/m08a_variants.py --repo . --base $BASE --out $M/variants --set "coalition.remove_countries=[$c]" \
          > $M/variants/variant_$c.log 2> $M/variants/variant_$c.err ); rc=$?
      r=$M/variants/integrated_minus${c}_2920_3h_VARIANT_RECEIPT.json; f=$M/variants/integrated_minus${c}_2920_3h_unsolved.nc
      log VARIANT_$c "exit=$rc:receipt=$($PY -c "import json,sys; print(json.load(open(sys.argv[1]))['output']['sha256'])" $r 2>/dev/null):file=$(sha256sum $f 2>/dev/null | cut -c1-64):$(grep -h Elapsed $M/variants/variant_$c.err | awk '{print $NF}')"
      cp -p $r $EV/variant_receipts/ 2>/dev/null
    done ;;
  loops)
    ( $PY $SCR/m12b_loops.py --full $BASE --variants $M/variants --out $EV/M12B_KVL_LOOPS.json > $M/loops.log 2>&1 ); log LOOPS "exit=$?:$(tail -1 $M/loops.log)" ;;
esac
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
log DONE_$STEP
