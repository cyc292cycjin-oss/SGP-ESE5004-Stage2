#!/bin/bash
# W08 checklist section 1: build the SDMX base in the W08 worktree and compare with the I2 scratch files (byte level).
set -u
R=/home/jin/wt_v4_w08; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $R || exit 1
export PYTHONHASHSEED=0
$PY scripts_project/v4_base_sdmx.py || exit 1
$PY scripts_project/v4_base_sdmx.py --gates || exit 1
echo "capsule vs I2 scratch:"; sha256sum research_inputs/assembly_v1/sources/SDMX_2019_CAPSULE.json /home/jin/v4i2/SDMX_2019_CAPSULE.json | cut -c1-16
echo "D1 base vs I2 d1_base_S5p.csv:"; sha256sum research_inputs/industry_v4/D1_BASE2019_SDMX.csv /home/jin/v4i2/d1_base_S5p.csv | cut -c1-16
echo "memo vs I1 committed:"; sha256sum research_inputs/assembly_v1/sources/SDMX_2019_BLEND_MEMO.csv /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/I1/BASE2019_SDMX/SDMX_2019_BLEND_MEMO.csv | cut -c1-16
git status --short | head -20
