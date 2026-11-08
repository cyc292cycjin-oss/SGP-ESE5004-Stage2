#!/bin/bash
# D2b section 5: the D2a network-ledger test (Fable F-05) on the D2b build (V4_D2A_BUILD points to it), plus the D2b table tests. No solver.
export V4_D2A_BUILD=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d2b/builds/main/integrated/integrated_365_24h_unsolved.nc
bash /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2b_20261108/scripts/ut.sh net_d2b tests/research/test_v4_d2a_fixes.py tests/research/test_v4_d2b_band.py tests/research/test_v4_d2b_biomass.py
