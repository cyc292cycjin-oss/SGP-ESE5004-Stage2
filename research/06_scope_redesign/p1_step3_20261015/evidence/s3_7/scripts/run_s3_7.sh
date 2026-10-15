#!/bin/bash
# S3-7: builds (both carbon modes), structural gap table, 56x3h smoke per mode and scenario, gap_diagnostic where infeasible,
# independent feasibility confirmation of the integrated main LP with HiGHS simplex (user supplement 2026-10-16).
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=results_project/s3_7
AUTH="S3 instruction S3-7 and user supplement 2026-10-16 (56x3h smoke both carbon modes, gap_diagnostic if infeasible, simplex confirmation of the integrated LP); smoke only"
mkdir -p $OUT/smoke $OUT/smoke_simplex $OUT/gap_diagnostic
: > $OUT/STATUS.txt
for sc in integrated disconnected; do
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/$sc --estimate-only > $OUT/${sc}_estimate.log 2> $OUT/${sc}_estimate.err
  echo "ESTIMATE_$sc:$?" >> $OUT/STATUS.txt
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/$sc > $OUT/${sc}_build.log 2> $OUT/${sc}_build.err
  echo "BUILD_$sc:$?" >> $OUT/STATUS.txt
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/pc_$sc --override s3.fuel_carbon_mode=producer_credit > $OUT/pc_${sc}_build.log 2> $OUT/pc_${sc}_build.err
  echo "BUILD_pc_$sc:$?" >> $OUT/STATUS.txt
done
$PY scripts_project/s2_structural_gap.py --network $OUT/integrated/integrated_2920_3h_unsolved.nc --network $OUT/disconnected/disconnected_2920_3h_unsolved.nc --output $OUT/S3_7_STRUCTURAL_GAP_ANNUAL.json > $OUT/structural_gap.log 2>&1
echo "GAPTABLE:$?" >> $OUT/STATUS.txt
# main mode smokes (IPM) + simplex confirmation of the integrated LP
/usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/integrated/integrated_2920_3h_unsolved.nc --scenario integrated --output $OUT/smoke/integrated --truncate 56 --label SMOKE_TEST_ONLY --authorization "$AUTH" --highs-ipm --time-limit 3600 > $OUT/smoke/integrated_solve.log 2> $OUT/smoke/integrated_solve.err
echo "SMOKE_integrated:$?" >> $OUT/STATUS.txt
/usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/integrated/integrated_2920_3h_unsolved.nc --scenario integrated --output $OUT/smoke_simplex/integrated --truncate 56 --label SMOKE_TEST_ONLY --authorization "$AUTH (simplex confirmation)" --time-limit 10800 > $OUT/smoke_simplex/integrated_solve.log 2> $OUT/smoke_simplex/integrated_solve.err
echo "SIMPLEX_integrated:$?" >> $OUT/STATUS.txt
/usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/disconnected/disconnected_2920_3h_unsolved.nc --scenario disconnected --output $OUT/smoke/disconnected --truncate 56 --label SMOKE_TEST_ONLY --authorization "$AUTH" --highs-ipm --time-limit 3600 > $OUT/smoke/disconnected_solve.log 2> $OUT/smoke/disconnected_solve.err
echo "SMOKE_disconnected:$?" >> $OUT/STATUS.txt
# producer_credit smokes (IPM)
for sc in integrated disconnected; do
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/pc_$sc/${sc}_2920_3h_unsolved.nc --scenario $sc --output $OUT/smoke/pc_$sc --truncate 56 --label SMOKE_TEST_ONLY --authorization "$AUTH (producer_credit sensitivity)" --highs-ipm --time-limit 3600 > $OUT/smoke/pc_${sc}_solve.log 2> $OUT/smoke/pc_${sc}_solve.err
  echo "SMOKE_pc_$sc:$?" >> $OUT/STATUS.txt
done
# gap diagnostics where the smoke was infeasible
for tag in integrated disconnected pc_integrated pc_disconnected; do
  sc=${tag#pc_}; ov=""; if [ "$tag" != "$sc" ]; then ov="--override s3.fuel_carbon_mode=producer_credit"; fi
  if grep -qi "infeasible" $OUT/smoke/$tag/SOLVE_RECEIPT.json 2>/dev/null; then
    $PY scripts_project/s2_network.py --scenario $sc --output $OUT/${tag}_gap --gap-diagnostic $ov > $OUT/${tag}_gap_build.log 2> $OUT/${tag}_gap_build.err
    echo "GAPBUILD_$tag:$?" >> $OUT/STATUS.txt
    /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/${tag}_gap/${sc}_gap_diagnostic_2920_3h_unsolved.nc --scenario $sc --output $OUT/gap_diagnostic/$tag --truncate 56 --label GAP_DIAGNOSTIC --authorization "$AUTH (gap_diagnostic, decisions 49/53)" --highs-ipm --time-limit 3600 > $OUT/gap_diagnostic/${tag}_solve.log 2> $OUT/gap_diagnostic/${tag}_solve.err
    echo "GAP_$tag:$?" >> $OUT/STATUS.txt
  else
    echo "GAP_$tag:skipped (smoke not infeasible)" >> $OUT/STATUS.txt
  fi
done
echo "DONE" >> $OUT/STATUS.txt
