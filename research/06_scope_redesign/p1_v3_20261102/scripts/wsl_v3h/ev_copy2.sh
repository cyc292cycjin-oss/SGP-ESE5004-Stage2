#!/bin/bash
# smoke evidence (light files only; the raw solve.log / solve.err carry licence banner lines and stay in results_project) + the S-A effect JSONs
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; R=$MAIN/results_project/v3hpc; E=/home/jin/wt_v3_hpc/research/06_scope_redesign/p1_v3_20261102/evidence/hpc
cp $R/evidence/*.json $E/
cp $R/smoke_hpc/STATUS.txt $E/smoke/SMOKE_STATUS_LOCAL.txt
for rid in integrated no_new_xb; do
  mkdir -p $E/smoke/$rid/m12_owen
  for f in SOLVE_RECEIPT.json V5_GATES.json V6_ACCEPTANCE.json V6_ACCEPTANCE_PROVISIONAL.json PRECISION.json PRECISION.md LEDGER_IDENTITY.json ALLOCATION.json STOP_CLASS.json GUROBI_LOG_SCRUBBED.txt COUNTRY_COST_LEDGER.csv EMISSIONS_BY_COUNTRY.json; do [ -f $R/smoke_hpc/$rid/$f ] && cp $R/smoke_hpc/$rid/$f $E/smoke/$rid/; done
  cp $R/smoke_hpc/$rid/m12_owen/*.json $E/smoke/$rid/m12_owen/ 2>/dev/null
done
[ -f $R/smoke_hpc/BATCH_REFERENCE.json ] && cp $R/smoke_hpc/BATCH_REFERENCE.json $E/smoke/
[ -d $R/smoke_hpc/M12_BENEFIT ] && { mkdir -p $E/smoke/M12_BENEFIT; cp $R/smoke_hpc/M12_BENEFIT/*.json $R/smoke_hpc/M12_BENEFIT/*.csv $E/smoke/M12_BENEFIT/ 2>/dev/null; }
grep -rIlE "licen[cs]e[[:space:]]*(id|key)|registered[[:space:]]+to|wls(access|secret)" $E/smoke | head -3; echo "licence-word files above (expect none)"
du -sh $E
