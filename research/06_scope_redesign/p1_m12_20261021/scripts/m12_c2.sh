#!/bin/bash
# M12 C2: right-hand-side audit (LP built with linopy, never solved). STEP=smoke | full365 | variants | loo365 | loo24
set -u
export PYTHONHASHSEED=0
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
REPO=/home/jin/wt_m12_20261021
RP=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
W=/mnt/d/ResearchWorkspaces/ASEAN/work
EV=$W/p1_m12_20261021/evidence/c2
LOC=/home/jin/m12_local
SMOKE=$RP/s4o/s4o3/solves/s4o_integrated
S4N=$W/p1_step4n_20261019/cloud_results/20261019T072454Z_5125/full/export/integrated
NET365=$RP/s4m/s4m3/builds/integrated/integrated_365_24h_unsolved.nc
mkdir -p "$EV" "$LOC"
cd "$REPO"
STEP=${STEP:?}
case "$STEP" in
  smoke)
    $PY scripts_project/m12_allocation.py run --repo "$REPO" --solve-dir "$SMOKE" --scenario integrated --label SMOKE_56x3h --out "$EV/smoke_alloc" > "$EV/smoke_alloc.log" 2>&1
    echo "ALLOC:exit=$?"
    /usr/bin/time -v $PY scripts_project/m12_rhs_audit.py audit --repo "$REPO" --network "$RP/s4m/s4m1/builds/integrated/integrated_2920_3h_unsolved.nc" --truncate 56 \
      --scenario integrated --solve-dir "$SMOKE" --allocation "$EV/smoke_alloc/ALLOCATION.json" --tag SMOKE_56x3h --out "$EV/smoke_56x3h" > "$EV/smoke_56x3h.log" 2> "$EV/smoke_56x3h.err"
    echo "AUDIT:exit=$?"
    ;;
  smoke_nc)   # same smoke model with rows-only duals (DUALS_BY_CONSTRAINT.nc) + solved flows: check of the rc rebuild and of the KVL transfer route
    $PY scripts_project/m12_rhs_audit.py audit --repo "$REPO" --network "$RP/s4m/s4m1/builds/integrated/integrated_2920_3h_unsolved.nc" --truncate 56 --scenario integrated \
      --duals "$SMOKE/DUALS_BY_CONSTRAINT.nc" --solved "$SMOKE/integrated_SMOKE_TEST_ONLY_solved.nc" --allocation "$EV/smoke_alloc/ALLOCATION.json" --tag SMOKE_56x3h_NC --out "$EV/smoke_56x3h_nc" > "$EV/smoke_56x3h_nc.log" 2>&1
    echo "AUDIT_NC:exit=$?"
    ;;
  full365)
    /usr/bin/time -v $PY scripts_project/m12_rhs_audit.py audit --repo "$REPO" --network "$NET365" --scenario integrated \
      --duals "$S4N/DUALS_BY_CONSTRAINT.nc" --solved "$S4N/integrated_FORMAL_TRIAL_365X24H_solved.nc" --allocation "$W/p1_m12_20261021/evidence/c43/s4n_integrated/ALLOCATION.json" --tag S4N_PILOT_365x24h --out "$EV/full_365x24h" > "$EV/full_365x24h.log" 2> "$EV/full_365x24h.err"
    echo "AUDIT365:exit=$?"
    ;;
  dis365)
    S4OD=$W/p1_step4o_20261019/cloud_results/20261019T162951Z_6896/full/unpacked/disconnected
    /usr/bin/time -v $PY scripts_project/m12_rhs_audit.py audit --repo "$REPO" --network "$RP/s4m/s4m3/builds/disconnected/disconnected_365_24h_unsolved.nc" --scenario disconnected \
      --duals "$S4OD/DUALS_BY_CONSTRAINT.nc" --solved "$S4OD/disconnected_FORMAL_TRIAL_365X24H_solved.nc" --allocation "$W/p1_m12_20261021/evidence/c43/s4o_disconnected/ALLOCATION.json" \
      --tag S4O6_DISCONNECTED_365x24h --out "$EV/disconnected_365x24h" > "$EV/disconnected_365x24h.log" 2> "$EV/disconnected_365x24h.err"
    echo "AUDIT_DIS365:exit=$?"
    ;;
  variants)
    for c in ${COUNTRIES:-VN}; do
      $PY scripts_project/m08a_variants.py --repo "$REPO" --base "$NET365" --out "$LOC/variants" --set "coalition.remove_countries=[$c]" --allow-stale-base > "$LOC/variant_$c.log" 2>&1
      echo "VARIANT_$c:exit=$?"
    done
    ;;
  loo365)
    c=${COUNTRY:-VN}
    /usr/bin/time -v $PY scripts_project/m12_rhs_audit.py audit --repo "$REPO" --network "$LOC/variants/integrated_minus${c}_365_24h_unsolved.nc" --scenario integrated \
      --tag "MINUS_${c}_365x24h" --out "$EV/minus_${c}_365x24h" > "$EV/minus_${c}_365x24h.log" 2> "$EV/minus_${c}_365x24h.err"
    echo "AUDIT_MINUS_$c:exit=$?"
    $PY scripts_project/m12_rhs_audit.py loo --full "$EV/full_365x24h/RHS_BY_FAMILY_OWNER.csv" --variant "$EV/minus_${c}_365x24h/RHS_BY_FAMILY_OWNER.csv" --removed "$c" --out "$EV/minus_${c}_365x24h" >> "$EV/minus_${c}_365x24h.log" 2>&1
    echo "LOO_$c:exit=$?"
    ;;
  loo24)
    T=${TRUNC:-24}
    $PY scripts_project/m12_rhs_audit.py audit --repo "$REPO" --network "$NET365" --scenario integrated --truncate "$T" --tag "FULL_trunc$T" --out "$EV/loo_trunc$T/full" > "$EV/loo_trunc$T.full.log" 2>&1
    echo "FULL_T:exit=$?"
    for c in ${COUNTRIES:-BN ID KH LA MM MY PH SG TH TL VN}; do
      $PY scripts_project/m12_rhs_audit.py audit --repo "$REPO" --network "$LOC/variants/integrated_minus${c}_365_24h_unsolved.nc" --scenario integrated --truncate "$T" \
        --tag "MINUS_${c}_trunc$T" --out "$EV/loo_trunc$T/minus_$c" > "$EV/loo_trunc$T.minus_$c.log" 2>&1
      $PY scripts_project/m12_rhs_audit.py loo --full "$EV/loo_trunc$T/full/RHS_BY_FAMILY_OWNER.csv" --variant "$EV/loo_trunc$T/minus_$c/RHS_BY_FAMILY_OWNER.csv" --removed "$c" --out "$EV/loo_trunc$T/minus_$c" >> "$EV/loo_trunc$T.minus_$c.log" 2>&1
      echo "LOO_$c:exit=$?:$(tail -1 $EV/loo_trunc$T.minus_$c.log)"
    done
    ;;
esac
grep -h -E "Maximum resident|Elapsed" "$EV"/*.err 2>/dev/null | tail -4
