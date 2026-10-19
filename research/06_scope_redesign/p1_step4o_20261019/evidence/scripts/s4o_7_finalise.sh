#!/bin/bash
# S4O stop report: copy report / progress into the repo step folder, evidence JSON back to the work folder, scan, stage
set -u
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
D=research/06_scope_redesign/p1_step4o_20261019; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019
cp $W/S4O_REPORT.md $W/S4O_PROGRESS.md $D/
cp /home/jin/s4o_syntax.sh /home/jin/s4o_7_finalise.sh $D/evidence/scripts/
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
$PY $D/evidence/scripts/s4o_collect_evidence.py . $D/S4O_EVIDENCE.json
cp $D/S4O_EVIDENCE.json $W/
chmod 755 $D/cloud_package/*.sh $D/evidence/s4o_4/*.sh $D/evidence/scripts/*.sh
bash /home/jin/s4o_scan.sh $D research/STAGE2_PROJECT_LEDGER.md $W 2>&1 | grep -vE "conda_explicit|environment_pypsa|ENV_"
for f in S4O_REPORT.md S4O_PROGRESS.md S4O_EVIDENCE.json; do cmp $W/$f $D/$f && echo "same: $f"; done
git add -f $D research/STAGE2_PROJECT_LEDGER.md
git status --short | grep -v '^??'
