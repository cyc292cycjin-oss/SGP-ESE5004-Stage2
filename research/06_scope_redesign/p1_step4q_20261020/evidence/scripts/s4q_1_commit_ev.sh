#!/bin/bash
set -u
W=/home/jin/wt_s4q_20261020; D=$W/research/06_scope_redesign/p1_step4q_20261020; SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4q_20261020
cd $W
cp $SRC/S4Q_PROGRESS.md $D/; chmod 644 $D/S4Q_CLAUDE_CODE_INSTRUCTION.md $D/S4Q_INSTRUCTION_SHA256.txt $D/S4Q_PROGRESS.md
cp /home/jin/s4q_1_script_tests.sh /home/jin/s4q_1_commit.sh $D/evidence/scripts/
H=$(grep -rIilE "license[i]d|registered[[:space:]]+to|wls(secret|accessid)" $D)
[ -z "$H" ] && echo "LICENCE_SCAN: no hit ($(find $D -type f | wc -l) files)" || { echo "LICENCE STRING FOUND:"; echo "$H"; exit 1; }
git add -f $D
git diff --cached --summary | head; git diff --cached --stat | tail -2
git commit -q -m "S4Q-1 evidence: script tests on 84532e78 - S4O harness 59/59 (FIXED_RUNS off, S4O behaviour unchanged; output in evidence/s4q_1/s4o4_rerun, S4O evidence untouched), S4Q cases N1-N6 8/8; unit-test diagnosis (worktree without git-ignored inputs: 2 failed / 63 skipped also at baseline 0b681881); progress; text file modes 644

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git log --oneline -1
git push -q -u origin codex/s4q-tol-calibration-20261020 2>&1 | tail -2; git ls-remote --heads origin codex/s4q-tol-calibration-20261020
