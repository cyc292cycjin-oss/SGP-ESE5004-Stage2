#!/bin/bash
# S4O supplement 01: report / progress into the repo step folder, evidence JSON (and back to the work folder), ledger already edited; scan; commit; push
set -euo pipefail
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
D=research/06_scope_redesign/p1_step4o_20261019; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019
cp $W/S4O_REPORT.md $W/S4O_PROGRESS.md $D/
cp /home/jin/s4o_s1_finalise.sh $D/evidence/scripts/
/home/jin/miniforge3/envs/pypsa-earth/bin/python $D/evidence/scripts/s4o_collect_evidence.py . $D/S4O_EVIDENCE.json
cp $D/S4O_EVIDENCE.json $W/
chmod 755 $D/evidence/scripts/*.sh
bash /home/jin/s4o_scan.sh $D research/STAGE2_PROJECT_LEDGER.md 2>&1 | grep -vE "conda_explicit|environment_pypsa"
for f in S4O_REPORT.md S4O_PROGRESS.md S4O_EVIDENCE.json; do cmp $W/$f $D/$f && echo "same: $f"; done
git add -f $D research/STAGE2_PROJECT_LEDGER.md
git diff --cached --stat | tail -3
git commit -q -F - <<'EOF'
S4O supplement 01 report: section 10 (decision 121 - S4O-2' profile A default, S4O-3' end-to-end check passed with objective difference 0.0, S4O-4 package at 126110ff with networks identical to f50c8850 and PACKAGE_DELTA.json upload 124.3 MB, S4O-5 estimate), evidence JSON, progress, ledger; stopped before S4O-6 (cloud not authorised)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
git push -q origin codex/s4o-production-20261019 2>&1 | tail -1
git ls-remote origin codex/s4o-production-20261019
