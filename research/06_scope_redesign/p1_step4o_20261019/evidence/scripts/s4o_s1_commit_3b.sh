#!/bin/bash
# S4O supplement 01: commit the S4O-3' evidence, the S4O-5 resource estimate, the make_package text update (decision 121) and the progress file
set -euo pipefail
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
D=research/06_scope_redesign/p1_step4o_20261019; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019
cp $W/S4O_PROGRESS.md $D/
cp /home/jin/s4o_s1_registry.sh /home/jin/s4o_s1_commit_code.sh /home/jin/s4o_s1_commit_3b.sh /home/jin/s4o_4_script_tests.sh /home/jin/s4o_4_package.sh $D/evidence/scripts/
chmod 755 $D/evidence/scripts/*.sh $D/cloud_package/*.sh
bash /home/jin/s4o_scan.sh $D/evidence/s4o_3b $D/CLOUD_RESOURCE_ESTIMATE.md 2>&1 | grep -vE "^== (IPv4|cloud|ssh|user|password|scan)" || true
git add -f $D/evidence/s4o_3b $D/evidence/s4o_4 $D/evidence/scripts $D/CLOUD_RESOURCE_ESTIMATE.md $D/cloud_package/make_package.sh $D/S4O_PROGRESS.md
git diff --cached --stat | tail -4
git commit -q -F - <<'EOF'
S4O supplement 01 S4O-3' (decision 121): local 56x3h end-to-end check of the S4O pipeline (run_365x24h.sh with TRUNCATE=56, default profile A, automatic C1) - optimal, objective relative difference to S4M-2 0.0, C1 in EXPORTS.json, grade equal to the S4O-2 equivalence (all accepted); S4O-5 resource estimate (CLOUD_RESOURCE_ESTIMATE.md section 23: 2920x3h LP 72.1 M rows, memory 106-165 GiB, 15-35 h per run on 8470Q, 2 AutoDL cards, data disk >= 100 GB, correction of the S4M section 22.5 over-estimate); make_package.sh manifest text for decision 121; script test results 59/59 and 9/9

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
