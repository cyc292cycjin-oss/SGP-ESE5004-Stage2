#!/bin/bash
# S3-1: build both scenarios with the gas network, annual structural gap table (no solver).
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=results_project/s3_1
mkdir -p $OUT
: > $OUT/STATUS.txt
for sc in integrated disconnected; do
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/$sc > $OUT/${sc}_build.log 2> $OUT/${sc}_build.err
  echo "BUILD_$sc:$?" >> $OUT/STATUS.txt
done
$PY scripts_project/s2_structural_gap.py --network $OUT/integrated/integrated_2920_3h_unsolved.nc --network $OUT/disconnected/disconnected_2920_3h_unsolved.nc --output $OUT/S3_1_STRUCTURAL_GAP_ANNUAL.json > $OUT/structural_gap.log 2>&1
echo "GAPTABLE:$?" >> $OUT/STATUS.txt
echo "DONE" >> $OUT/STATUS.txt
