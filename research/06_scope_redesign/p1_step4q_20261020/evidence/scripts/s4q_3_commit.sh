#!/bin/bash
set -u
W=/home/jin/wt_s4q_20261020; D=$W/research/06_scope_redesign/p1_step4q_20261020; E=$D/evidence/s4q_3; SH=/home/jin/s4q_local/judge_shadow
cd $W
for t in t8 t16; do for sc in integrated disconnected integrated_nze; do mkdir -p $E/shadow_c1_s4m2_reference/$t/$sc; cp $SH/$t/$sc/PRECISION.json $SH/$t/$sc/PRECISION.md $E/shadow_c1_s4m2_reference/$t/$sc/; done; done
bash /home/jin/s4q_3_gates.sh > $E/GATES_INFORMATION.txt 2>&1; bash /home/jin/s4q_3_gates2.sh > $E/GATES_B2_B14_A3_C1_TERMS.txt 2>&1; bash /home/jin/s4q_3_info.sh > $E/INFORMATION_SUMMARY.txt 2>&1
grep -v "Command being\|PROJ" $E/judge_stderr.txt | grep -E "Elapsed|Maximum resident|Error|Traceback" > $E/judge_time.txt; rm -f $E/judge_stderr.txt
cp /home/jin/s4q_3_judge.sh /home/jin/s4q_3_info.sh /home/jin/s4q_3_gates.sh /home/jin/s4q_3_gates2.sh /home/jin/s4q_2_commit.sh $D/evidence/scripts/
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $D)
[ -z "$H" ] && echo "LICENCE_SCAN: no hit" || { echo "LICENCE STRING FOUND: $H"; exit 1; }
git add -f $D; git diff --cached --stat | tail -1
git commit -q -m "S4Q-3 (decision 123 point (5), criteria fixed beforehand): verdict LEVEL 1 PASSED on both paths - Threads 8 and Threads 16: all six runs optimal with C1 (a)(b)(c) passed against the S4M-2 per-country reference (re-graded on shadow copies, run folders unchanged); objective vs profile A +2.5e-9 .. +4.8e-9 (<= 1e-5), B16 <= 4.7e-10 (<= 1e-6); country differences and NZE entity totals change <= 0.0002 bn (tolerance >= 0.01 bn); information: iterations / WU 0.67-0.94 of profile A, prices and CO2 / biomass shadow prices within 0.1 EUR, the two paths differ by <= 9.2e-10; project gates (information) A1_A2_S4B fail on all six (dual-sign errors ~1e-4 vs budget 1e-5); judge script s4q_judge.py, compare outputs, evidence

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git log --oneline -1 | cut -c1-90
