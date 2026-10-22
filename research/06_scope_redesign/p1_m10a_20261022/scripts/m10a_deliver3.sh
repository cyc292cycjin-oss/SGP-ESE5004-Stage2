#!/bin/bash
# M10A commit 3: report wording + progress (work copies -> repo mirror), push, licence-string rescan
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10a_20261022; R=/home/jin/wt_m10p_20261022/research/06_scope_redesign/p1_m10a_20261022
cp $W/M10A_REPORT.md $W/M10A_PROGRESS.md $R/ || exit 1
cp /home/jin/m10a_deliver.sh /home/jin/m10a_deliver3.sh $W/scripts/; cp $W/scripts/m10a_deliver.sh $W/scripts/m10a_deliver3.sh $R/scripts/
cd /home/jin/wt_m10p_20261022 || exit 1
git add -A -- research/06_scope_redesign/p1_m10a_20261022
git status --short | head
git commit -q -F /home/jin/m10a_msg3.txt && echo "COMMIT3 $(git rev-parse HEAD)" || echo "COMMIT3 nothing"
git push origin codex/m10-batch3-20261022 2>&1 | tail -2; echo "PUSH_EXIT ${PIPESTATUS[0]}"
echo "licence-like strings in the committed M10A evidence (expect none):"
grep -rIilE 'license[i]d|registered[[:space:]]+to|wls(secret|accessid)' research/06_scope_redesign/p1_m10a_20261022 research/06_scope_redesign/p1_m10p_20261022/evidence/m10a_v4; echo "(end)"
git status --porcelain --untracked-files=no | wc -l; git log --oneline -4
