#!/bin/bash
# run the electric-base tests of test_s4a_profiles in the worktree with a temporary read-only link to the main checkout's electric base
WT=/home/jin/wt_m08a_20261021
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
cd $WT || exit 1
[ -e results_project/assembly_v1 ] && { echo "results_project/assembly_v1 exists in the worktree - abort"; exit 2; }
mkdir -p results_project/assembly_v1/final_assets
ln -s $MAIN/results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc
/home/jin/miniforge3/envs/pypsa-earth/bin/python -m pytest -q -p no:cacheprovider tests/research/test_s4a_profiles.py -rs 2>&1 | grep -E "^E |passed|failed|FAILED|SKIPPED" | head -20
rm results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc; rmdir results_project/assembly_v1/final_assets results_project/assembly_v1
ls -A results_project; git status --short | head
