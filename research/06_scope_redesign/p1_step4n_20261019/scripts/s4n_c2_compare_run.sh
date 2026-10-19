#!/bin/bash
# C2 comparison (read-only) + evidence copy (light files) + licence scan
set -u
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/evidence/s4n_c2; mkdir -p $E
export PYTHONHASHSEED=0; unset GRB_LICENSE_FILE
cd $RM
$PY /mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/scripts/s4n_c2_compare.py --repo $RM --ref results_project/s4m/s4m2/solves --cal results_project/s4n/s4n_c2/solves \
   --builds results_project/s4m/s4m1/builds --ref-duals-integrated results_project/s4m/s4ms2/solves/s4m_A_integrated_rerun \
   --out-json $E/C2_CALIBRATION.json --out-md $E/C2_CALIBRATION.md 2>&1 | grep -v "PROJ\|Warning\|warn"
cp results_project/s4n/s4n_c2/STATUS.txt $E/STATUS.txt
for t in cal_integrated cal_disconnected cal_integrated_nze; do mkdir -p $E/$t; d=results_project/s4n/s4n_c2/solves/$t
  for f in SOLVE_RECEIPT.json V5_GATES.json GUROBI_LOG_SCRUBBED.txt COUNTRY_COST_LEDGER.csv LEDGER_IDENTITY.json EXPORTS.json INTERIOR_CHECKS.json; do [ -f $d/$f ] && cp $d/$f $E/$t/; done
  cp $d.solve_log_scrubbed.txt $E/$t/solve_log_scrubbed.txt 2>/dev/null
  grep -A 25 "Command being timed" $d.solve.err | grep -viE "licen[cs]e|registered|wls|academic" > $E/$t/solve_time.txt
done
cp /home/jin/s4n_c2_run.sh $E/RUN_SCRIPT_s4n_c2_run.sh
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $E)
[ -z "$H" ] && echo "LICENCE_SCAN_C2_EVIDENCE: no hit ($(find $E -type f | wc -l) files)" || { echo "LICENCE STRING FOUND:"; echo "$H"; }
