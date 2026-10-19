#!/bin/bash
# S4O-3 points 2-3 (read only, no solver): (1) final profile vs S4M-2 profile A with the decision-107 standard fixed beforehand (objective <= 1e-5,
# B16 <= 1e-6, country difference change <= max(1 %, 0.01 bn)); (2) final profile vs the S4N C2 calibration (threads 32, lowercase keys) - information only.
# Uses the S4N comparison tool unchanged (research/06_scope_redesign/p1_step4n_20261019/scripts/s4n_c2_compare.py). Evidence copy (light files) + licence scan.
set -u
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
TOOL=$RM/research/06_scope_redesign/p1_step4n_20261019/scripts/s4n_c2_compare.py
E=$RM/research/06_scope_redesign/p1_step4o_20261019/evidence/s4o_3; mkdir -p $E
export PYTHONHASHSEED=0; unset GRB_LICENSE_FILE
cd $RM
$PY $TOOL --repo $RM --ref results_project/s4m/s4m2/solves --cal results_project/s4o/s4o3/solves --cal-tag s4o_ \
   --builds results_project/s4m/s4m1/builds --ref-duals-integrated results_project/s4m/s4ms2/solves/s4m_A_integrated_rerun \
   --out-json $E/S4O3_VS_S4M2_PROFILE_A.json --out-md $E/S4O3_VS_S4M2_PROFILE_A.md 2>&1 | grep -v "PROJ\|Warning\|warn" | tail -5
echo "== information only: vs S4N C2 (threads 32, lowercase keys)"
$PY $TOOL --repo $RM --ref results_project/s4n/s4n_c2/solves --ref-tag cal_ --cal results_project/s4o/s4o3/solves --cal-tag s4o_ \
   --builds results_project/s4m/s4m1/builds \
   --out-json $E/S4O3_VS_S4N_C2_INFO.json --out-md $E/S4O3_VS_S4N_C2_INFO.md 2>&1 | grep -v "PROJ\|Warning\|warn" | tail -5
S=results_project/s4o/s4o3
cp $S/STATUS.txt $E/STATUS.txt; cp $S/BATCH_REFERENCE.json $E/ 2>/dev/null
for t in s4o_integrated s4o_disconnected s4o_integrated_nze; do mkdir -p $E/$t; d=$S/solves/$t
  for f in SOLVE_RECEIPT.json V5_GATES.json GUROBI_LOG_SCRUBBED.txt COUNTRY_COST_LEDGER.csv LEDGER_IDENTITY.json EXPORTS.json INTERIOR_CHECKS.json PRECISION.json PRECISION.md VIOLATIONS.json; do [ -f $d/$f ] && cp $d/$f $E/$t/; done
  cp $d.solve_log_scrubbed.txt $E/$t/solve_log_scrubbed.txt 2>/dev/null
  grep -A 25 "Command being timed" $d.solve.err | grep -viE "licen[cs]e|registered|wls|academic" > $E/$t/solve_time.txt
  for k in c1_va c1; do grep -E "Elapsed|Maximum resident" $d.$k.err > $E/$t/${k}_time.txt 2>/dev/null; done
done
cp /home/jin/s4o_3_run.sh /home/jin/s4o_3_compare.sh $RM/research/06_scope_redesign/p1_step4o_20261019/evidence/scripts/
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $E)
[ -z "$H" ] && echo "LICENCE_SCAN_S4O3_EVIDENCE: no hit ($(find $E -type f | wc -l) files)" || { echo "LICENCE STRING FOUND:"; echo "$H"; }
