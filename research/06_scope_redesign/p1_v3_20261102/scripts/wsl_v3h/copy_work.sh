#!/bin/bash
# copy the V3 HPC deliverables of the branch to work/p1_v3_20261102/ (instruction step 6; user supplement 3): the files of this session at any time; the three shared
# files only after the V27 shutdown record (read and confirmed 2026-11-04: second shutdown 02:12:51 SGT) and only while their work/ copy still equals the base 5e372e5d
# (so that nothing of another session is overwritten). Nothing is deleted; the copy is verified file by file.
set -u
W=/home/jin/wt_v3_hpc; D=research/06_scope_redesign/p1_v3_20261102; WK=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102
cd $W || exit 2
grep -q "02:12:51 关机" "$WK/V3_PROGRESS.md" && grep -q "补充 07 全部完成" "$WK/V3_PROGRESS.md" || { echo "REFUSED: the V27 shutdown record is not in V3_PROGRESS.md"; exit 2; }
NEW="V3_HPC_PROGRESS.md RUN_PLAN_HPC_V3.md HPC_OPERATOR_GUIDE_V3.md V3_REPORT_HPC_PACKAGE.md batch_def/BATCH_DEF_2920x3h_v3hpc.json hpc_v3 evidence/hpc scripts/wsl_v3h"
SHARED="RUN_PLAN_V3.md V3_RULES.md batch_def/BATCH_DEF_2920x3h.json"
for f in $SHARED; do
  [ "$(sha256sum < "$WK/$f")" = "$(git show "5e372e5d:$D/$f" | sha256sum)" ] || { echo "REFUSED: work/$f differs from the base 5e372e5d (changed by another session) - not overwritten"; exit 2; }
done
for f in $NEW $SHARED; do
  mkdir -p "$WK/$(dirname "$f")"
  if [ -d "$D/$f" ]; then mkdir -p "$WK/$f" && cp -rp "$D/$f/." "$WK/$f/"; else cp -p "$D/$f" "$WK/$f"; fi
done
bad=0
for f in $NEW $SHARED; do
  if [ -d "$D/$f" ]; then
    while IFS= read -r g; do cmp -s "$D/$f/$g" "$WK/$f/$g" || { echo "DIFF: $f/$g"; bad=$((bad + 1)); }; done < <(cd "$D/$f" && find . -type f | sed 's#^\./##')
  else cmp -s "$D/$f" "$WK/$f" || { echo "DIFF: $f"; bad=$((bad + 1)); }; fi
done
echo "copied: $(for f in $NEW $SHARED; do [ -d "$D/$f" ] && (cd "$D/$f" && find . -type f | wc -l) || echo 1; done | paste -sd+ - | bc) files; differences after copy: $bad"
