#!/bin/bash
# V3 supplement 06: run the read-only probe on the networks (no solver)
free -g | head -2; nproc
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3
X=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T063207Z/full_unpacked/export
ls $R/builds_op/integrated/
cd /home/jin/wt_v3_20261102
PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/v3e/probe.py $R/builds_op/integrated/integrated_2920_3h_unsolved.nc $R/builds_op/integrated/integrated_365_24h_unsolved.nc $X/V1/integrated_DFX_365X24H_solved.nc $R/smoke_s5/integrated/integrated_SMOKE_TEST_ONLY_solved.nc 2>&1 | grep -v Warning
