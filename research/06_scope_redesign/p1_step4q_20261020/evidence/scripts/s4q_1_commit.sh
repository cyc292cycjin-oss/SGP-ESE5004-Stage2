#!/bin/bash
set -u
W=/home/jin/wt_s4q_20261020; D=$W/research/06_scope_redesign/p1_step4q_20261020; SRC=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4q_20261020
MSG=/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/db7f254d-3f62-4a49-ab56-2f4a5ec3d4f9/scratchpad/msg_s4q1.txt
cd $W
[ "$(git branch --show-current)" = codex/s4q-tol-calibration-20261020 ] || { echo "REFUSED: wrong branch"; exit 2; }
mkdir -p $D/evidence/scripts
cp $SRC/S4Q_CLAUDE_CODE_INSTRUCTION.md $SRC/S4Q_INSTRUCTION_SHA256.txt $SRC/S4Q_PROGRESS.md $D/
(cd $D && sha256sum -c S4Q_INSTRUCTION_SHA256.txt)
chmod 755 research/06_scope_redesign/p1_step4o_20261019/cloud_package/run_365x24h.sh $D/evidence/s4q_1/test_s4q1_pipeline.sh
cp /home/jin/s4q_1_tests.sh /home/jin/s4q_1_testdiag.sh $D/evidence/scripts/
git add configs/research/baseline.yaml tests/research/test_s4q_1.py research/06_scope_redesign/p1_step4o_20261019/cloud_package/run_365x24h.sh $D
git diff --cached --summary; git diff --cached --stat
git commit -q -F $MSG && git log --oneline -1
