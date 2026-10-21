#!/bin/bash
# M12 supplement 01 evidence (item 136): LPs BUILT with linopy, never solved; no Gurobi, no cloud. Outputs in NEW folders only.
#   STEP=toy | smoke | s4n365 | s4o365 | benefit         pre-correction runs (S4N pilot integrated + S4O-6 disconnected), dual form as main value
#   STEP=m08b_int | m08b_dis                              C2 audit on the M08b (PR #47) 365x24h networks (structure; no duals exist yet)
#   STEP=m08b_variants [COUNTRIES=...]                    leave-one-out variants from the M08b integrated network with the M08b worktree's
#                                                         m08a_variants.py, NO --allow-stale-base (base must match the M08b config)
#   STEP=m08b_loo365 [COUNTRIES="VN TH LA"] | m08b_loo24  structural leave-one-out checks (365x24h; others on a 24-snapshot truncation)
set -u
export PYTHONHASHSEED=0
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
REPO=/home/jin/wt_m12_20261021
M08B=/home/jin/wt_m08b_20261021
RP=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
W=/mnt/d/ResearchWorkspaces/ASEAN/work
EV=$W/p1_m12_20261021/evidence
S01=$EV/s01; SB=$EV/s01_m08b
LOC=/home/jin/m12_local
NETS=$LOC/m08b_s01_nets   # M08b supplement-01 rebuild at ec80668f (integrated 75704334..., disconnected 888a009b...); matches the M08b worktree code
echo "M08B_HEAD:$(cd "$M08B" && git rev-parse HEAD):dirty=$(cd "$M08B" && git status --porcelain | wc -l)"
SMOKE=$RP/s4o/s4o3/solves/s4o_integrated
S4N=$W/p1_step4n_20261019/cloud_results/20261019T072454Z_5125/full/export/integrated
S4O=$W/p1_step4o_20261019/cloud_results/20261019T162951Z_6896
NET365=$RP/s4m/s4m3/builds/integrated/integrated_365_24h_unsolved.nc
DIS365=$RP/s4m/s4m3/builds/disconnected/disconnected_365_24h_unsolved.nc
mkdir -p "$S01" "$SB" "$LOC"
cd "$REPO"
STEP=${STEP:?}
A="$REPO/scripts_project/m12_rhs_audit.py"
case "$STEP" in
  toy)
    $PY "$W/p1_m12_20261021/scripts/m12_s01_toy_evidence.py" --repo "$REPO" --out "$S01/toy" > "$S01/toy.log" 2>&1; echo "TOY:exit=$?"
    ;;
  smoke)
    /usr/bin/time -v $PY "$A" audit --repo "$REPO" --network "$RP/s4m/s4m1/builds/integrated/integrated_2920_3h_unsolved.nc" --truncate 56 --scenario integrated \
      --solve-dir "$SMOKE" --allocation "$EV/c2/smoke_alloc/ALLOCATION.json" --tag SMOKE_56x3h --out "$S01/smoke_56x3h" > "$S01/smoke_56x3h.log" 2> "$S01/smoke_56x3h.err"
    echo "SMOKE:exit=$?"
    ;;
  s4n365)
    /usr/bin/time -v $PY "$A" audit --repo "$REPO" --network "$NET365" --scenario integrated --duals "$S4N/DUALS_BY_CONSTRAINT.nc" \
      --solved "$S4N/integrated_FORMAL_TRIAL_365X24H_solved.nc" --allocation "$EV/c43/s4n_integrated/ALLOCATION.json" --precision "$S4O/top/pilot_integrated/PRECISION.json" \
      --tag S4N_PILOT_365x24h --out "$S01/s4n_pilot_365x24h" > "$S01/s4n_pilot_365x24h.log" 2> "$S01/s4n_pilot_365x24h.err"
    echo "S4N365:exit=$?"
    ;;
  s4o365)
    D=$S4O/full/unpacked/disconnected
    /usr/bin/time -v $PY "$A" audit --repo "$REPO" --network "$DIS365" --scenario disconnected --duals "$D/DUALS_BY_CONSTRAINT.nc" \
      --solved "$D/disconnected_FORMAL_TRIAL_365X24H_solved.nc" --allocation "$EV/c43/s4o_disconnected/ALLOCATION.json" --precision "$D/PRECISION.json" \
      --tag S4O6_DISCONNECTED_365x24h --out "$S01/s4o6_disconnected_365x24h" > "$S01/s4o6_disconnected_365x24h.log" 2> "$S01/s4o6_disconnected_365x24h.err"
    echo "S4O365:exit=$?"
    ;;
  benefit)
    $PY scripts_project/m12_allocation.py benefit --repo "$REPO" --integrated "$EV/c43/s4n_integrated" --disconnected "$EV/c43/s4o_disconnected" --out "$S01/benefit_pre_correction" \
      --integrated-dual "$S01/s4n_pilot_365x24h/OWEN.json" --disconnected-dual "$S01/s4o6_disconnected_365x24h/OWEN.json" > "$S01/benefit_pre_correction.log" 2>&1
    echo "BENEFIT:exit=$?"
    ;;
  m08b_int|m08b_dis)
    sc=integrated; [ "$STEP" = m08b_dis ] && sc=disconnected
    /usr/bin/time -v $PY "$A" audit --repo "$M08B" --network "$NETS/${sc}_365_24h_unsolved.nc" --scenario $sc --tag "M08B_${sc}_365x24h" \
      --out "$SB/${sc}_365x24h" > "$SB/${sc}_365x24h.log" 2> "$SB/${sc}_365x24h.err"
    echo "M08B_$sc:exit=$?"
    ;;
  m08b_variants)
    mkdir -p "$LOC/m08b_variants" "$SB/variant_receipts"
    for c in ${COUNTRIES:-VN TH LA BN ID KH MM MY PH SG TL}; do
      ( cd "$M08B" && /usr/bin/time -v $PY scripts_project/m08a_variants.py --repo "$M08B" --base "$NETS/integrated_365_24h_unsolved.nc" --out "$LOC/m08b_variants" \
          --set "coalition.remove_countries=[$c]" > "$LOC/m08b_variants/variant_$c.log" 2> "$LOC/m08b_variants/variant_$c.err" )
      echo "VARIANT_$c:exit=$?:$(grep -h Elapsed "$LOC/m08b_variants/variant_$c.err" | tr -s ' ')"
      cp -p "$LOC/m08b_variants/integrated_minus${c}_365_24h_VARIANT_RECEIPT.json" "$SB/variant_receipts/" 2>/dev/null
    done
    ;;
  m08b_loo365)
    for c in ${COUNTRIES:-VN TH LA}; do
      /usr/bin/time -v $PY "$A" audit --repo "$M08B" --network "$LOC/m08b_variants/integrated_minus${c}_365_24h_unsolved.nc" --scenario integrated \
        --tag "M08B_MINUS_${c}_365x24h" --out "$SB/minus_${c}_365x24h" > "$SB/minus_${c}_365x24h.log" 2> "$SB/minus_${c}_365x24h.err"
      echo "AUDIT_MINUS_$c:exit=$?"
      $PY "$A" loo --full "$SB/integrated_365x24h/RHS_BY_FAMILY_OWNER.csv" --variant "$SB/minus_${c}_365x24h/RHS_BY_FAMILY_OWNER.csv" --removed "$c" \
        --out "$SB/minus_${c}_365x24h" >> "$SB/minus_${c}_365x24h.log" 2>&1
      echo "LOO_$c:exit=$?:$(tail -1 "$SB/minus_${c}_365x24h.log")"
    done
    ;;
  m08b_loo24)
    T=${TRUNC:-24}
    $PY "$A" audit --repo "$M08B" --network "$NETS/integrated_365_24h_unsolved.nc" --scenario integrated --truncate "$T" --tag "M08B_FULL_trunc$T" \
      --out "$SB/loo_trunc$T/full" > "$SB/loo_trunc$T.full.log" 2>&1
    echo "FULL_T:exit=$?"
    for c in ${COUNTRIES:-BN ID KH MM MY PH SG TL}; do
      $PY "$A" audit --repo "$M08B" --network "$LOC/m08b_variants/integrated_minus${c}_365_24h_unsolved.nc" --scenario integrated --truncate "$T" \
        --tag "M08B_MINUS_${c}_trunc$T" --out "$SB/loo_trunc$T/minus_$c" > "$SB/loo_trunc$T.minus_$c.log" 2>&1
      $PY "$A" loo --full "$SB/loo_trunc$T/full/RHS_BY_FAMILY_OWNER.csv" --variant "$SB/loo_trunc$T/minus_$c/RHS_BY_FAMILY_OWNER.csv" --removed "$c" \
        --out "$SB/loo_trunc$T/minus_$c" >> "$SB/loo_trunc$T.minus_$c.log" 2>&1
      echo "LOO_$c:exit=$?:$(tail -1 "$SB/loo_trunc$T.minus_$c.log")"
    done
    ;;
esac
grep -h -E "Maximum resident|Elapsed" "$S01"/*.err "$SB"/*.err 2>/dev/null | tail -4
