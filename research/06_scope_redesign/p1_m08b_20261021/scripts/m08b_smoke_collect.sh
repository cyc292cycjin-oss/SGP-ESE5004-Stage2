#!/bin/bash
# M08b section 4: copy the lightweight smoke evidence (no solver logs, no stdout / stderr) and scan the copies for licence-like strings
set -u
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/smoke
E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08b_20261021/evidence/smoke
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'
mkdir -p $E
cp $R/STATUS.txt $E/SMOKE_STATUS.txt; cp $R/BATCH_REFERENCE.json $E/
for s in integrated disconnected; do
  mkdir -p $E/$s
  for f in SOLVE_RECEIPT.json V5_GATES.json V6_ACCEPTANCE.json PRECISION.json PRECISION.md LEDGER_IDENTITY.json COUNTRY_COST_LEDGER.csv EXPORTS.json INTERIOR_CHECKS.json; do
    [ -f $R/$s/$f ] && cp $R/$s/$f $E/$s/
  done
done
echo "licence-pattern hits in the copies (file:count):"
grep -r -c -i -E "$SCRUB" $E | grep -v ':0$' || echo "none"
du -sh $E
