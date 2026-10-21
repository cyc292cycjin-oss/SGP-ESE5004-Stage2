#!/bin/bash
cd /home/jin/wt_m08a_20261021/scripts_project || exit 1
PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python /mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08a_20261021/scripts/m08a_b1_evidence.py \
  --repo /home/jin/wt_m08a_20261021 \
  --base /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4m/s4m3/builds/disconnected/disconnected_2920_3h_unsolved.nc \
  --scratch /home/jin/m08a_scratch_b1 --out /mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08a_20261021 2>&1 | grep -v -E "Warning|warn\(|^INFO|PROJ"
echo "exit=${PIPESTATUS[0]}"
