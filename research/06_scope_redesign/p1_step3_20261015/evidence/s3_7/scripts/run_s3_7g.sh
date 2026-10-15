#!/bin/bash
# S3-7 (decision 65): Gurobi 56x3h smokes for both carbon modes x both scenarios, gap_diagnostic where infeasible.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s3_7/gurobi
AUTH="decision 65 (user authorization 2026-10-16): Gurobi 12.0.3 WLS academic licence, 56x3h smoke both carbon modes x both scenarios, gap_diagnostic if infeasible; smoke only"
mkdir -p $OUT/smoke $OUT/gap_diagnostic
: > $OUT/STATUS.txt
for tag in integrated disconnected pc_integrated pc_disconnected; do
  sc=${tag#pc_}; ov=""; if [ "$tag" != "$sc" ]; then ov="--override s3.fuel_carbon_mode=producer_credit"; fi
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network results_project/s3_7/$tag/${sc}_2920_3h_unsolved.nc --scenario $sc --output $OUT/smoke/$tag --truncate 56 --label SMOKE_TEST_ONLY --authorization "$AUTH" --solver gurobi --time-limit 3600 > $OUT/smoke/${tag}_solve.log 2> $OUT/smoke/${tag}_solve.err
  echo "GSMOKE_$tag:$?" >> $OUT/STATUS.txt
  if grep -qi "infeasible" $OUT/smoke/$tag/SOLVE_RECEIPT.json 2>/dev/null; then
    if [ ! -f results_project/s3_7/${tag}_gap/${sc}_gap_diagnostic_2920_3h_unsolved.nc ]; then
      $PY scripts_project/s2_network.py --scenario $sc --output results_project/s3_7/${tag}_gap --gap-diagnostic $ov > results_project/s3_7/${tag}_gap_build.log 2> results_project/s3_7/${tag}_gap_build.err
      echo "GAPBUILD_$tag:$?" >> $OUT/STATUS.txt
    fi
    /usr/bin/time -v $PY scripts_project/s2_solve.py --network results_project/s3_7/${tag}_gap/${sc}_gap_diagnostic_2920_3h_unsolved.nc --scenario $sc --output $OUT/gap_diagnostic/$tag --truncate 56 --label GAP_DIAGNOSTIC --authorization "$AUTH (gap_diagnostic, decisions 49/53)" --solver gurobi --time-limit 3600 > $OUT/gap_diagnostic/${tag}_solve.log 2> $OUT/gap_diagnostic/${tag}_solve.err
    echo "GGAP_$tag:$?" >> $OUT/STATUS.txt
  else
    echo "GGAP_$tag:skipped (smoke not infeasible)" >> $OUT/STATUS.txt
  fi
done
echo "DONE" >> $OUT/STATUS.txt
