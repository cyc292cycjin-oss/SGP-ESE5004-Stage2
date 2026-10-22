#!/bin/bash
# M10A supplement 01 delivery: mirror the work folder into the repo, commit (message /home/jin/m10a_s01_msg2.txt), push, licence-string rescan
set -u
WT=/home/jin/wt_m10p_20261022; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10a_20261022
R=$WT/research/06_scope_redesign/p1_m10a_20261022; R10=$WT/research/06_scope_redesign/p1_m10p_20261022/evidence/m10a_v5
mkdir -p $R/evidence $R/scripts $R10 $W/scripts
cp /home/jin/m10a_s01_*.sh /home/jin/m10a_s01_buildcmp.py /home/jin/m10a_dryrun_v5.sh $W/scripts/ 2>/dev/null
cp $W/M10A_REPORT.md $W/M10A_EVIDENCE.json $W/M10A_PROGRESS.md $W/M10A_SUPPLEMENT_01.md $W/M10A_SUPPLEMENT_01_SHA256.txt $R/
cp -r $W/evidence/. $R/evidence/
cp $W/scripts/m10a_*.sh $W/scripts/m10a_s01_buildcmp.py $R/scripts/ 2>/dev/null
for f in PACKAGE_MANIFEST.json SHA256SUMS VARIANT_REPRODUCIBILITY.json EXPECTED_VARIANTS.json BUILD_INPUT_CHANGES.json COMMIT PACKAGE_V5_VS_V3_V4.json; do cp $W/evidence/package_v5/$f $R10/; done
cd $WT || exit 1
for f in $R/evidence/b3b4/*.err $R/evidence/dryrun_v5/post_smoke/*/*.txt; do [ -f "$f" ] && grep -qiE 'licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic' "$f" && echo "SCRUB NEEDED: $f"; done
FORCE=$(git status --ignored --porcelain -- research/06_scope_redesign/p1_m10a_20261022 research/06_scope_redesign/p1_m10p_20261022/evidence/m10a_v5 | grep '^!!' | sed 's/^!! //' | tr '\n' ' ')
git add -A -- research/06_scope_redesign/p1_m10a_20261022 research/06_scope_redesign/p1_m10p_20261022/evidence/m10a_v5 || exit 1
[ -n "$FORCE" ] && git add -f -- $FORCE
echo "staged: $(git status --short | wc -l)"
git commit -q -F /home/jin/m10a_s01_msg2.txt || { echo "COMMIT_FAILED"; exit 1; }
echo "COMMIT $(git rev-parse HEAD)"
git push origin codex/m10-batch3-20261022 2>&1 | tail -2; echo "PUSH_EXIT ${PIPESTATUS[0]}"
echo "licence-like strings in the committed M10A evidence (expect none):"
grep -rIilE 'license[i]d|registered[[:space:]]+to|wls(secret|accessid)' research/06_scope_redesign/p1_m10a_20261022 research/06_scope_redesign/p1_m10p_20261022/evidence/m10a_v5; echo "(end)"
git status --porcelain --untracked-files=no | wc -l; git log --oneline -4
echo S01_DELIVER_DONE
