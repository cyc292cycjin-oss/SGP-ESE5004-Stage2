#!/bin/bash
# S4N-1 evidence: copy the light files to the work folder (no network / dual arrays / raw logs), then scan the evidence folder for licence strings.
set -u
S=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4n/s4n1; D=$S/solve
E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/evidence/s4n_1
mkdir -p $E
for f in SOLVE_RECEIPT.json V5_GATES.json EXPORTS.json DUALS_INDEX.csv GUROBI_LOG_SCRUBBED.txt COMPONENT_COST_BREAKDOWN_SUMMARY.json LEDGER_IDENTITY.json RESOURCE.jsonl; do cp $D/$f $E/; done
cp $S/STATUS.txt $S/S4N1_CHECK.json $S/solve_log_scrubbed.txt $E/
grep -v PROJ $S/check.log > $E/check_log.txt
cp /home/jin/s4n1_run.sh $E/RUN_SCRIPT_s4n1_run.sh
grep -A 30 "Command being timed" $S/solve.err | grep -viE "licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic" > $E/solve_time.txt
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)|academic license" $E)
[ -z "$H" ] && echo "LICENCE_SCAN_EVIDENCE: no hit" || { echo "LICENCE STRING FOUND:"; echo "$H"; }
ls -la $E | awk 'NR>1 {print $5, $NF}'
du -sh $E | cut -f1
