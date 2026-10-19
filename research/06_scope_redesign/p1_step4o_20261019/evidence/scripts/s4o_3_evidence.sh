#!/bin/bash
# S4O-3 evidence copy (light files of the one run made) + licence scan; the comparison tool is not run (it needs all three scenarios; stopped)
set -u
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
E=$RM/research/06_scope_redesign/p1_step4o_20261019/evidence/s4o_3; mkdir -p $E
S=$RM/results_project/s4o/s4o3
cp $S/STATUS.txt $E/STATUS.txt
t=s4o_integrated; mkdir -p $E/$t; d=$S/solves/$t
for f in SOLVE_RECEIPT.json V5_GATES.json GUROBI_LOG_SCRUBBED.txt COUNTRY_COST_LEDGER.csv LEDGER_IDENTITY.json EXPORTS.json INTERIOR_CHECKS.json PRECISION.json PRECISION.md VIOLATIONS.json; do [ -f $d/$f ] && cp $d/$f $E/$t/; done
cp $d/v5/kkt_summary.json $E/$t/ 2>/dev/null
cp $d.solve_log_scrubbed.txt $E/$t/solve_log_scrubbed.txt
grep -A 25 "Command being timed" $d.solve.err | grep -viE "licen[cs]e|registered|wls|academic" > $E/$t/solve_time.txt
for k in c1_va c1; do grep -E "Elapsed|Maximum resident" $d.$k.err > $E/$t/${k}_time.txt 2>/dev/null; done
cp /home/jin/s4o_3_run.sh /home/jin/s4o_3_after_stop.sh /home/jin/s4o_3_readonly_info.sh /home/jin/s4o_3_compare.sh /home/jin/s4o_3_evidence.sh /home/jin/s4o_4_checks_dry.sh $RM/research/06_scope_redesign/p1_step4o_20261019/evidence/scripts/
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $E)
[ -z "$H" ] && echo "LICENCE_SCAN_S4O3_EVIDENCE: no hit ($(find $E -type f | wc -l) files)" || { echo "LICENCE STRING FOUND:"; echo "$H"; }
du -sh $E
