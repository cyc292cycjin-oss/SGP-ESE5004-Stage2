#!/bin/bash
set -u
cd /home/jin/wt_v3_hpc
export PYTHONHASHSEED=0
T0=$(date +%s)
bash research/06_scope_redesign/p1_v3_20261102/hpc_v3/make_hpc_package_v3.sh /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3hpc/builds /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3 2>&1 | tail -15
echo "PKG_EXIT:${PIPESTATUS[0]}:$(( $(date +%s) - T0 ))s"
