#!/bin/bash
set -u
W=/home/jin/wt_s4q_20261020; D=$W/research/06_scope_redesign/p1_step4q_20261020; SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4q_20261020; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W
cp $SRC/S4Q_REPORT.md $SRC/S4Q_PROGRESS.md $D/; chmod 644 $D/S4Q_REPORT.md $D/S4Q_PROGRESS.md
$PY $D/scripts/s4q_collect_evidence.py --deliv $D --repo $W --out $D/S4Q_EVIDENCE.json | cut -c1-300
cp $D/S4Q_EVIDENCE.json $SRC/
mkdir -p $SRC/evidence_s4q_3; cp $D/evidence/s4q_3/S4Q3_JUDGE.md $D/evidence/s4q_3/S4Q3_JUDGE.json $SRC/evidence_s4q_3/
cp /home/jin/s4q_4_table.sh /home/jin/s4q_4_refs.sh /home/jin/s4q_4_co2.sh /home/jin/s4q_3_commit.sh /home/jin/s4q_4_commit.sh $D/evidence/scripts/
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $D research/STAGE2_PROJECT_LEDGER.md)
[ -z "$H" ] && echo "LICENCE_SCAN: no hit" || { echo "LICENCE STRING FOUND: $H"; exit 1; }
grep -rIlE "([0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}|ssh -p|@region|seetacloud" $D --include=*.md --include=*.sh --include=*.json --include=*.txt | head -3
git add -f $D research/STAGE2_PROJECT_LEDGER.md; git diff --cached --stat | tail -1
git commit -q -m "S4Q-4 (decision 123): report S4Q_REPORT.md - LEVEL 1 PASSED on both paths (Threads 8 and Threads 16, all six runs optimal, criteria 1-4 of decision 123 point (5) passed without adjustment); information items, findings (A1_A2_S4B gate on the candidate, B2 / B14 noise, test harness exit-in-eval); level-2 plan (PROPOSED, not executed: 4 cloud 365x24h runs, references, time 6-11 h, cost with unit price DATA_PENDING, merging with S4P re-runs, efficiency-standard method); S4Q_EVIDENCE.json (s4q_collect_evidence.py), progress, ledger entry

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git log --oneline -1 | cut -c1-80
git push -q origin codex/s4q-tol-calibration-20261020 2>&1 | tail -1; git ls-remote --heads origin codex/s4q-tol-calibration-20261020 | cut -c1-12; git status --short | head -5
