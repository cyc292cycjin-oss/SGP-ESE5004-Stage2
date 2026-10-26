#!/bin/bash
# DFX phase 4: copy the evidence of the recovered results into the deliverable folder (evidence/phase4). Key files of the light pack only (the packs
# themselves stay in the work folder cloud_results/), the analysis outputs, the pack SHA256 files, the upload / download / test logs and the filtered
# instance records (written by the caller to $2). No host / port anywhere.
#   bash p4_evidence.sh <cloud_results/<tag> dir> <instance records txt>
set -u
C=${1:?}; R=${2:?}
D=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026/evidence/phase4
X=$C/light_unpacked/export
mkdir -p $D/batch/M12_BENEFIT $D/instance
cp $X/batch/DFX_SUMMARY.json $X/batch/DFX_SUMMARY.md $X/batch/BATCH_REFERENCE.json $X/batch/BASE_CHECK.json $X/batch/ARRAYS_MANIFEST.json $X/batch/STATUS.txt $D/batch/
cp $X/batch/M12_BENEFIT/* $D/batch/M12_BENEFIT/
for r in V1 V2; do
  mkdir -p $D/$r/m12_owen
  for f in RUN.json SOLVE_RECEIPT.json V5_GATES.json V6_ACCEPTANCE.json V6_ACCEPTANCE_PROVISIONAL.json PRECISION.json PRECISION.md VIOLATIONS.json \
           LEDGER_IDENTITY.json INTERIOR_CHECKS.json kkt_summary.json COUNTRY_COST_LEDGER.csv COUNTRY_COST_LEDGER_USD2020.csv EMISSIONS_BY_COUNTRY.json \
           BUNKER_ACCOUNT.json ALLOCATION.json ALLOCATION.md GUROBI_LOG_SCRUBBED.txt solve_time.txt MONITOR_$r.csv MATH_PROBLEM.json; do
    [ -f $X/$r/$f ] && cp $X/$r/$f $D/$r/
  done
  cp $X/$r/m12_owen/OWEN.json $X/$r/m12_owen/OWEN.md $X/$r/m12_owen/OWEN.csv $X/$r/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json $X/$r/m12_owen/RHS_AUDIT.json $D/$r/m12_owen/
done
cp $C/analysis/DFX_PHASE4_RESULTS.json $C/analysis/DFX_PHASE4_TABLES.md $D/
cp $C/*.sha256 $D/
cp /home/jin/dfx4/upload.log $D/instance/UPLOAD.log
cp /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/tests/pre_upload.log $D/instance/PRE_UPLOAD_TESTS.log
awk -v d=$D/instance '/^@@FILE /{f=d "/" $2; next} /^@@END/{f=""} f!="" {print > f}' "$R"
[ -s $D/instance/RUN_DFX_CONSOLE.log ] || rm -f $D/instance/RUN_DFX_CONSOLE.log
mv $D/instance/STATUS.txt $D/instance/STATUS_FINAL.txt 2>/dev/null
find $D -type f | sort | sed "s|$D/||" > /tmp/p4_ev_list.txt; echo "files: $(wc -l < /tmp/p4_ev_list.txt)"; du -sh $D
