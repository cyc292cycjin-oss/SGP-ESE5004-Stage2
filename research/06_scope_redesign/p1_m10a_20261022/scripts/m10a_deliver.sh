#!/bin/bash
# M10A delivery: mirror the work folder into the repo, commit 2 (message /home/jin/m10a_msg2.txt), push the branch (origin = project repo)
set -u
WT=/home/jin/wt_m10p_20261022; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10a_20261022; W10=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022
R=$WT/research/06_scope_redesign/p1_m10a_20261022; R10=$WT/research/06_scope_redesign/p1_m10p_20261022/evidence/m10a_v4
mkdir -p $R/evidence $R/scripts $R10 $W/scripts
cp /home/jin/m10a_*.sh $W/scripts/
cp $W/M10A_REPORT.md $W/M10A_EVIDENCE.json $W/M10A_PROGRESS.md $W/M10A_CLAUDE_CODE_INSTRUCTION.md $W/M10A_INSTRUCTION_SHA256.txt $R/
cp -r $W/evidence/. $R/evidence/
cp $W/scripts/m10a_*.sh $R/scripts/
cp $W/evidence/package_v4/PACKAGE_MANIFEST.json $W/evidence/package_v4/SHA256SUMS $W/evidence/package_v4/VARIANT_REPRODUCIBILITY.json $W/evidence/package_v4/EXPECTED_VARIANTS.json $W/evidence/package_v4/BUILD_INPUT_CHANGES.json $W/evidence/package_v4/COMMIT $W/evidence/package_v4/PACKAGE_V4_VS_V3.json $R10/
cd $WT || exit 1
echo "--- ignored files under the new folders (will be force-added) ---"
git status --ignored --porcelain -- research/06_scope_redesign/p1_m10a_20261022 research/06_scope_redesign/p1_m10p_20261022/evidence/m10a_v4 | grep '^!!' | head -30
FORCE=$(git status --ignored --porcelain -- research/06_scope_redesign/p1_m10a_20261022 research/06_scope_redesign/p1_m10p_20261022/evidence/m10a_v4 | grep '^!!' | sed 's/^!! //' | tr '\n' ' ')
git add -A -- research/06_scope_redesign/p1_m10a_20261022 research/06_scope_redesign/p1_m10p_20261022/evidence/m10a_v4 || exit 1
[ -n "$FORCE" ] && git add -f -- $FORCE
git status --short | wc -l
git commit -q -F /home/jin/m10a_msg2.txt || { echo "COMMIT2_FAILED"; exit 1; }
echo "COMMIT2 $(git rev-parse HEAD)"
git push origin codex/m10-batch3-20261022 2>&1 | tail -5; echo "PUSH_EXIT ${PIPESTATUS[0]}"
git log --oneline -3; git status --porcelain --untracked-files=no | wc -l
echo DELIVER_DONE
