#!/bin/bash
# M10A supplement 01 follow-up: report summary line + progress -> repo mirror, commit (message /home/jin/m10a_s01_msg3.txt), push, placeholder check
set -u
WT=/home/jin/wt_m10p_20261022; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10a_20261022; R=$WT/research/06_scope_redesign/p1_m10a_20261022
cp $W/M10A_REPORT.md $W/M10A_PROGRESS.md $R/ || exit 1
cp /home/jin/m10a_s01_deliver2.sh $W/scripts/ && cp /home/jin/m10a_s01_deliver2.sh $R/scripts/
cd $WT || exit 1
echo "placeholders left in the repo copies (expect none):"; grep -n "S01-DRY\|S01-MIN\|S01-PKG\|S01-C1\|待填" $R/M10A_REPORT.md $R/M10A_PROGRESS.md $R/M10A_EVIDENCE.json; echo "(end)"
git add -A -- research/06_scope_redesign/p1_m10a_20261022
git commit -q -F /home/jin/m10a_s01_msg3.txt && echo "COMMIT $(git rev-parse HEAD)" || echo "COMMIT nothing"
git push origin codex/m10-batch3-20261022 2>&1 | tail -2; echo "PUSH_EXIT ${PIPESTATUS[0]}"
git status --porcelain --untracked-files=no | wc -l; git log --oneline -3
