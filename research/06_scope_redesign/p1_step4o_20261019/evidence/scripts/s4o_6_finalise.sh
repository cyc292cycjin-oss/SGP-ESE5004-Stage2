#!/bin/bash
# S4O-6 / S4O-7 close-out: report and progress into the repo, evidence JSON, licence / login-pattern scan, commit, push
set -euo pipefail
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
D=research/06_scope_redesign/p1_step4o_20261019; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019
cp $W/S4O_REPORT.md $W/S4O_PROGRESS.md $W/S4O_SUPPLEMENT_02.md $W/S4O_SUPPLEMENT_02_SHA256.txt $D/
cp /home/jin/s4o_6_finalise.sh /home/jin/s4o_scan_split.sh $D/evidence/scripts/
/home/jin/miniforge3/envs/pypsa-earth/bin/python $D/evidence/scripts/s4o_collect_evidence.py . $D/S4O_EVIDENCE.json
cp $D/S4O_EVIDENCE.json $W/
chmod 755 $D/evidence/scripts/*.sh
bash /home/jin/s4o_scan.sh $D research/STAGE2_PROJECT_LEDGER.md 2>&1 | grep -vE "conda_explicit|environment_pypsa|ENV_|=1\.1\.|=0\.9\.15"
for f in S4O_REPORT.md S4O_PROGRESS.md S4O_EVIDENCE.json; do cmp $W/$f $D/$f && echo "same: $f"; done
git add -f $D research/STAGE2_PROJECT_LEDGER.md
git diff --cached --stat | tail -2
git commit -q -F - <<'EOF'
S4O-6 / S4O-7 (supplement 02, unattended): 365x24h batch on an 8481C clone (probe r 0.836, profile A, 21,600 / 22,500 s) - disconnected STEPS, disconnected diagnostic and integrated NZE all SUBOPTIMAL (no retry), C1 (a)(b)(c) passed for all three (reference = this batch's disconnected - S4N pilot integrated); B6 69.243 bn EUR, NZE - integrated -90.491 bn; results recovered and verified (full batch 461.0 MB, light package, two per-run packages), licence deleted; report section 11 with automatic decisions D1-D13, evidence s4o_6, progress, ledger

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
git push -q origin codex/s4o-production-20261019 2>&1 | tail -1
git ls-remote origin codex/s4o-production-20261019
