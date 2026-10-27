#!/bin/bash
# HPR: copy the deliverable folder of the worktree to the Windows work folder (plan, reports, checklist, review, evidence, scripts, package sources).
# Never touches the instruction files or other work folders; the built package hpc_package/ on D: is written by make_hpc_package.sh itself.
set -u
D=/home/jin/wt_hpr_20261027/research/06_scope_redesign/p1_hpr_20261027; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_hpr_20261027
for f in RUN_PLAN_HPC.md HPR_PROGRESS.md HPR_REPORT.md HPR_EVIDENCE.json PRE_HPC_CHECKLIST.md INDEPENDENT_REVIEW.md HPC_OPERATOR_GUIDE.md REFERENCE_VALUES.json; do [ -f $D/$f ] && cp $D/$f $W/; done
mkdir -p $W/hpc_package_src $W/scripts/wsl_hpr $W/evidence
cp -r $D/hpc_package_src/. $W/hpc_package_src/ 2>/dev/null
cp -r $D/scripts/wsl_hpr/. $W/scripts/wsl_hpr/ 2>/dev/null
cp -r $D/evidence/. $W/evidence/ 2>/dev/null
ls -la $W | head -40; du -sh $W
