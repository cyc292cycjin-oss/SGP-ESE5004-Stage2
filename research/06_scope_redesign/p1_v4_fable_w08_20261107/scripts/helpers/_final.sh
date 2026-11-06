#!/bin/bash
# Fable W08 review, stage 5: EVIDENCE.json -> commit 2 -> review zip + manifest -> PROGRESS final line -> commit 3 -> push.
set -u
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_fable_w08_20261107; WT=/home/jin/wt_v4_fable; BR=codex/v4-fable-w08-20261107
cd $S || exit 1
$PY scripts/build_evidence.py $S "6abe892fade3e6a4093e20efb9ba7ea74da47b7e (stage 3 commit; later commits in PROGRESS.md)" $BR || { echo "EVIDENCE FAILED"; exit 1; }
ls -la EVIDENCE.json
bash scripts/helpers/_commit1.sh _commit_msg2.txt | tail -4 || exit 1
C2=$(git -C $WT rev-parse HEAD); echo "COMMIT2 $C2"
$PY scripts/make_review_zip.py $S $C2 || { echo "ZIP FAILED"; exit 1; }
echo "- 12 最终提交链：第 3 节 6abe892f → 第 4–5 节 $C2 → 清单与本行（见 git log 最新提交）；审阅包 REVIEW_${C2:0:8}.zip（zip 不入库，清单 evidence/REVIEW_ZIP_MANIFEST_${C2:0:8}.txt 入库）。推送到 origin/$BR 后停止，等审阅。" >> PROGRESS.md
bash scripts/helpers/_commit1.sh _commit_msg3.txt | tail -3 || exit 1
C3=$(git -C $WT rev-parse HEAD); echo "COMMIT3 $C3"
cd $WT && git push origin $BR 2>&1 | tail -2
echo "remote: $(git ls-remote origin refs/heads/$BR | cut -c1-40)  local: $(git rev-parse HEAD)"
git log --oneline -4
git status --short | head -3; echo "(status above must be empty)"
ls -la $S/*.zip
