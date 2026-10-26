#!/bin/bash
# DFX v3: copy the deliverable folder of the worktree to the Windows work folder (reports, evidence, rules, plan, code map, scripts, HPC draft).
# Never touches the package dist (cloud_package_dfx on D: is the built package), the instruction files or the other work folders.
set -u
D=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026
for f in CODE_MAP.md CODE_MAP_TABLE.csv CODE_MAP_DATA.json DFX_RULES.md DFX_RULES_NUMBERS.json RUN_PLAN_DFX.md DFX_PROGRESS.md SECTION0_LEFTOVERS.md BATCH3_REFERENCE_VALUES.json \
         DFX_REPORT_PHASE1.md DFX_REPORT_PHASE2.md DFX_REPORT_PHASE3.md DFX_EVIDENCE.json PRE_AUTODL_CHECKLIST.md; do [ -f $D/$f ] && cp $D/$f $W/; done
mkdir -p $W/hpc_package_dfx $W/cloud_package_dfx_src $W/scripts/wsl_dfx3 $W/evidence
cp -r $D/hpc_package_dfx/. $W/hpc_package_dfx/; cp $D/cloud_package_dfx/*.sh $W/cloud_package_dfx_src/; cp -r $D/scripts/wsl_dfx3/. $W/scripts/wsl_dfx3/
cp $D/evidence/*.json $W/evidence/ 2>/dev/null
ls -la $W | head -40; du -sh $W
