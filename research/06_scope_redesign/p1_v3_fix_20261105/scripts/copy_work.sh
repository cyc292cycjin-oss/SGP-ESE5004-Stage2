#!/bin/bash
# Copy the V3.1 deliverables into work/p1_v3_20261102/ after checking that the files to be overwritten equal the branch base 7d22dda1 (no other session changed them).
set -u
WT=/home/jin/wt_v3_fix; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102; R=research/06_scope_redesign/p1_v3_20261102; BASE=7d22dda1
cd $WT
ok=1
for f in RUN_PLAN_HPC_V3.md HPC_OPERATOR_GUIDE_V3.md; do
  if cmp -s <(git show $BASE:$R/$f) $W/$f; then echo "work/$f = $BASE"; else echo "work/$f DIFFERS from $BASE - not overwritten"; ok=0; fi
done
# V3_HPC_PROGRESS.md is only appended to (final line); V14 appended its own final lines after 7d22dda1 (branch codex/v3-hpc-20261104 head 865c119c)
cmp -s <(git show origin/codex/v3-hpc-20261104:$R/V3_HPC_PROGRESS.md) $W/V3_HPC_PROGRESS.md && echo "work/V3_HPC_PROGRESS.md = codex/v3-hpc-20261104 head (append only)" || { echo "work/V3_HPC_PROGRESS.md changed by another session - stop"; ok=0; }
for f in batch_def/BATCH_DEF_2920x3h_v31hpc.json hpc_v31 V3_REPORT_FIX.md; do [ -e $W/$f ] && { echo "work/$f exists already - not overwritten"; ok=0; }; done
[ $ok = 1 ] || { echo "COPY_REFUSED"; exit 3; }
cp $R/RUN_PLAN_HPC_V3.md $R/HPC_OPERATOR_GUIDE_V3.md $W/
cp $R/batch_def/BATCH_DEF_2920x3h_v31hpc.json $W/batch_def/
mkdir -p $W/hpc_v31 && cp $R/hpc_v31/make_hpc_package_v31.sh $R/hpc_v31/fullsize_presolve.sh $W/hpc_v31/
cp research/06_scope_redesign/p1_v3_fix_20261105/V3_REPORT_FIX.md $W/
for f in RUN_PLAN_HPC_V3.md HPC_OPERATOR_GUIDE_V3.md batch_def/BATCH_DEF_2920x3h_v31hpc.json hpc_v31/make_hpc_package_v31.sh hpc_v31/fullsize_presolve.sh; do cmp -s $R/$f $W/$f && echo "copied $f" || echo "COPY MISMATCH $f"; done
cmp -s research/06_scope_redesign/p1_v3_fix_20261105/V3_REPORT_FIX.md $W/V3_REPORT_FIX.md && echo "copied V3_REPORT_FIX.md"
echo COPY_DONE
