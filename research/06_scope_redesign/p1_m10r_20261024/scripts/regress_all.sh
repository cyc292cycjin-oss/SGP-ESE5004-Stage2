#!/bin/bash
# M10R B2.3: run regress.sh (no solve) on every local 56x3h dataset with the CURRENT worktree code; TAG = pre | post.
set -u
TAG=${1:?pre|post}
M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=$M/m08b/builds_s01; S=$M/m08b/smoke_s01; V=$M/m12b/variants; R=$M/m10r/regress_$TAG; REF=$S/BATCH_REFERENCE.json
jget() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'): d=d.get(k) if isinstance(d, dict) else None
print(d)" "$1" "$2"; }
mkdir -p $R; echo "START $(date -u +%FT%TZ)" > $R/ALL_STATUS.txt
run() { bash /home/jin/m10r/regress.sh "$@" > "$R/$7.log" 2>&1; echo "$7 exit=$? $(date -u +%FT%TZ)" >> $R/ALL_STATUS.txt; }
run $S/integrated    $B/integrated/integrated_2920_3h_unsolved.nc       integrated   "$(jget $B/integrated/integrated_BUILD_RECEIPT.json network.sha256)"       $REF $R/integrated    integrated
run $S/disconnected  $B/disconnected/disconnected_2920_3h_unsolved.nc   disconnected "$(jget $B/disconnected/disconnected_BUILD_RECEIPT.json network.sha256)"   $REF $R/disconnected  disconnected
for c in VN TH LA; do
  run $M/m12b/integrated_minus$c $V/integrated_minus${c}_2920_3h_unsolved.nc integrated "$(jget $V/integrated_minus${c}_2920_3h_VARIANT_RECEIPT.json output.sha256)" $REF $R/minus$c minus$c
done
run $M/m10r/keepstock_v5 $M/m10r/variants/disconnected_keepstock_2920_3h_unsolved.nc disconnected "$(jget $M/m10r/variants/disconnected_keepstock_2920_3h_VARIANT_RECEIPT.json output.sha256)" $REF $R/keepstock keepstock
echo "DONE $(date -u +%FT%TZ)" >> $R/ALL_STATUS.txt
cat $R/ALL_STATUS.txt
