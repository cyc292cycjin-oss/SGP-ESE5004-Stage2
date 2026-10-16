#!/bin/bash
# S3-0.5: build both scenarios, annual structural gap table, 56x3h smoke (decision-58 weights), gap_diagnostic if infeasible.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=results_project/s3
AUTH="S3 instruction S3-0.5 (decisions 61-64 confirmed; user message 2026-10-15) smoke only"
mkdir -p $OUT/smoke $OUT/gap_diagnostic
: > $OUT/STATUS.txt
for sc in integrated disconnected; do
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/$sc --estimate-only > $OUT/${sc}_estimate.log 2> $OUT/${sc}_estimate.err
  echo "ESTIMATE_$sc:$?" >> $OUT/STATUS.txt
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/$sc > $OUT/${sc}_build.log 2> $OUT/${sc}_build.err
  echo "BUILD_$sc:$?" >> $OUT/STATUS.txt
done
$PY scripts_project/s2_structural_gap.py --network $OUT/integrated/integrated_2920_3h_unsolved.nc --network $OUT/disconnected/disconnected_2920_3h_unsolved.nc --output $OUT/S3_STRUCTURAL_GAP_ANNUAL.json > $OUT/structural_gap.log 2>&1
echo "GAPTABLE:$?" >> $OUT/STATUS.txt
for sc in integrated disconnected; do
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/$sc/${sc}_2920_3h_unsolved.nc --scenario $sc --output $OUT/smoke/$sc --truncate 56 --label SMOKE_TEST_ONLY --authorization "$AUTH" --highs-ipm --time-limit 3600 > $OUT/smoke/${sc}_solve.log 2> $OUT/smoke/${sc}_solve.err
  echo "SMOKE_$sc:$?" >> $OUT/STATUS.txt
  if grep -qi "infeasible" $OUT/smoke/$sc/SOLVE_RECEIPT.json; then
    $PY scripts_project/s2_network.py --scenario $sc --output $OUT/${sc}_gap --gap-diagnostic > $OUT/${sc}_gap_build.log 2> $OUT/${sc}_gap_build.err
    echo "GAPBUILD_$sc:$?" >> $OUT/STATUS.txt
    /usr/bin/time -v $PY scripts_project/s2_solve.py --network $OUT/${sc}_gap/${sc}_gap_diagnostic_2920_3h_unsolved.nc --scenario $sc --output $OUT/gap_diagnostic/$sc --truncate 56 --label GAP_DIAGNOSTIC --authorization "$AUTH (gap_diagnostic, decisions 49/53)" --highs-ipm --time-limit 3600 > $OUT/gap_diagnostic/${sc}_solve.log 2> $OUT/gap_diagnostic/${sc}_solve.err
    echo "GAP_$sc:$?" >> $OUT/STATUS.txt
  else
    echo "GAP_$sc:skipped (smoke not infeasible)" >> $OUT/STATUS.txt
  fi
done
echo "DONE" >> $OUT/STATUS.txt
