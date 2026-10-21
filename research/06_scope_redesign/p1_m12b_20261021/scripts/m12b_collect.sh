#!/bin/bash
# M12b: copy light evidence from results_project/m12b (git-ignored) into work/p1_m12b_20261021/evidence. STEP=prep | runs
# Solve logs are never copied raw (licence banner): GUROBI_LOG_SCRUBBED.txt only, and the folder is scanned for licence strings at the end.
set -u
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; M=$MAIN/results_project/m12b; SMOKE=$MAIN/results_project/m08b/smoke_s01
EV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12b_20261021/evidence
mkdir -p $EV
case "${STEP:?}" in
  prep)
    cp -p $M/PREP_STATUS.txt $EV/
    for sc in integrated disconnected; do
      d=$EV/full_$sc; mkdir -p $d
      cp -p $M/full_$sc/ALLOCATION.json $M/full_$sc/ALLOCATION.md $M/full_$sc/ALLOCATION.csv $d/ 2>/dev/null
      cp -p $M/full_$sc/ALLOCATION_LINES.csv $d/ 2>/dev/null
      cp -p $M/full_$sc/m12_owen/OWEN.json $M/full_$sc/m12_owen/OWEN.md $M/full_$sc/m12_owen/OWEN.csv $M/full_$sc/m12_owen/RHS_AUDIT.json \
            $M/full_$sc/m12_owen/RHS_FAMILY_SUMMARY.csv $d/ 2>/dev/null
    done
    # SHA256 of the reused run files (M08b smoke_s01, read through symlinks)
    { echo "scenario,file,bytes,sha256"
      for sc in integrated disconnected; do
        for f in SOLVE_RECEIPT.json PRECISION.json V6_ACCEPTANCE.json VIOLATIONS.json COUNTRY_COST_LEDGER.csv ${sc}_SMOKE_TEST_ONLY_solved.nc \
                 lp/MATH_PROBLEM.json lp/clabels.npy lp/vlabels.npy lp/cost.npy lp/index.npy lp/value.npy lp/start.npy lp/row_lower.npy lp/row_upper.npy \
                 lp/col_lower.npy lp/col_upper.npy solution/X.npy solution/Pi.npy solution/RC.npy; do
          p=$SMOKE/$sc/$f; echo "$sc,$f,$(stat -c %s $p),$(sha256sum $p | cut -c1-64)"
        done
      done
      echo "batch,BATCH_REFERENCE.json,$(stat -c %s $SMOKE/BATCH_REFERENCE.json),$(sha256sum $SMOKE/BATCH_REFERENCE.json | cut -c1-64)"
      echo "batch,STATUS.txt,$(stat -c %s $SMOKE/STATUS.txt),$(sha256sum $SMOKE/STATUS.txt | cut -c1-64)"
    } > $EV/M12B_REUSED_RUN_FILES.csv
    cp -p $SMOKE/STATUS.txt $EV/REUSED_SMOKE_S01_STATUS.txt
    { echo "country,file,bytes,sha256"
      for f in $M/variants/*_unsolved.nc; do c=$(basename $f | sed 's/integrated_minus\(..\)_.*/\1/'); echo "$c,$(basename $f),$(stat -c %s $f),$(sha256sum $f | cut -c1-64)"; done
    } > $EV/M12B_VARIANT_FILES.csv ;;
  runs)
    cp -p $M/STATUS.txt $EV/RUN_STATUS.txt
    for d in $M/integrated_minus*; do
      t=$(basename $d); o=$EV/runs/$t; mkdir -p $o
      for f in SOLVE_RECEIPT.json PRECISION.json PRECISION.md V6_ACCEPTANCE.json INTERIOR_CHECKS.json GUROBI_LOG_SCRUBBED.txt ALLOCATION.json ALLOCATION.md \
               ALLOCATION_LINES.csv EXPORTS.json c1_precision.log; do [ -f $d/$f ] && cp -p $d/$f $o/; done
      for f in OWEN.json OWEN.md RHS_AUDIT.json RHS_FAMILY_SUMMARY.csv; do [ -f $d/m12_owen/$f ] && cp -p $d/m12_owen/$f $o/; done
      [ -f $d/m12_loo_rhs/LOO_RHS_CHECK.json ] && cp -p $d/m12_loo_rhs/LOO_RHS_CHECK.json $o/
    done
    mkdir -p $EV/loo_check; cp -p $M/LOO_CHECK/LOO_CHECK.json $M/LOO_CHECK/LOO_CHECK.md $EV/loo_check/ 2>/dev/null ;;
esac
n=$(grep -rliE 'wlsaccess|wlssecret|licenseid|registered[[:space:]]+to' $EV | wc -l); echo "licence-string files in evidence: $n"
