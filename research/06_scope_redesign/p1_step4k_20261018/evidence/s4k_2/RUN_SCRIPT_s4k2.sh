#!/bin/bash
# S4K-2 static review: four networks (2920x3h + 365x24h) at the committed S4K-1 code, the S4I audit on the 365x24h networks and the S4K-2 review
# against the S4J networks of supplement 01 (a) (results_project/s4j/s4j3b); read only, no solve.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=results_project/s4k/s4k2; mkdir -p $OUT/builds $OUT/networks; ST=$OUT/STATUS.txt; : > $ST
echo "START:$(date -u +%FT%TZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" >> $ST
build() { local tag=$1 sc=$2; shift 2; mkdir -p $OUT/builds/$tag
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/builds/$tag "$@" > $OUT/builds/${tag}_build.log 2> $OUT/builds/${tag}_build.err
  echo "BUILD_$tag:$?:$(tail -1 $OUT/builds/${tag}_build.log | cut -c1-60):$(grep -h 'Maximum resident' $OUT/builds/${tag}_build.err | tr -s ' '):daily=$(ls $OUT/builds/$tag/*_365_24h_unsolved.nc 2>/dev/null | wc -l)" >> $ST
  grep -h "Error\|Traceback" $OUT/builds/${tag}_build.err | tail -3 >> $ST; }
build integrated integrated
build disconnected disconnected
build integrated_nze integrated --override fuels.price_scenario=nze
build disconnected_gap disconnected --gap-diagnostic
cp $OUT/builds/integrated/integrated_365_24h_unsolved.nc $OUT/networks/integrated_365_24h_unsolved.nc
cp $OUT/builds/disconnected/disconnected_365_24h_unsolved.nc $OUT/networks/disconnected_365_24h_unsolved.nc
cp $OUT/builds/integrated_nze/integrated_365_24h_unsolved.nc $OUT/networks/integrated_nze_365_24h_unsolved.nc
cp $OUT/builds/disconnected_gap/disconnected_gap_diagnostic_365_24h_unsolved.nc $OUT/networks/disconnected_gap_diagnostic_365_24h_unsolved.nc
cp $OUT/builds/integrated/integrated_BUILD_RECEIPT.json $OUT/networks/integrated_BUILD_RECEIPT.json
cp $OUT/builds/disconnected/disconnected_BUILD_RECEIPT.json $OUT/networks/disconnected_BUILD_RECEIPT.json
cp $OUT/builds/integrated_nze/integrated_BUILD_RECEIPT.json $OUT/networks/integrated_nze_BUILD_RECEIPT.json
cp $OUT/builds/disconnected_gap/disconnected_gap_diagnostic_BUILD_RECEIPT.json $OUT/networks/disconnected_gap_diagnostic_BUILD_RECEIPT.json
$PY scripts_project/s4i_static_audit.py --networks $OUT/networks --out $OUT/audit/static > $OUT/audit_static.log 2>&1; echo "AUDIT_STATIC:$?" >> $ST
$PY scripts_project/s4i_followups.py --networks $OUT/networks --out $OUT/audit/followups > $OUT/audit_followups.log 2>&1; echo "AUDIT_FOLLOWUPS:$?" >> $ST
(cd scripts_project && $PY s4k_2_review.py --ref-audit ../results_project/s4j/s4j3b/audit --audit ../$OUT/audit --ref-networks ../results_project/s4j/s4j3b/networks \
   --networks ../$OUT/networks --out ../$OUT/review > ../$OUT/review.log 2>&1); echo "REVIEW:$?" >> $ST
grep -h "Error\|Traceback" $OUT/review.log | tail -3 >> $ST
echo "DONE:$(date -u +%FT%TZ)" >> $ST
grep -v PROJ $ST
