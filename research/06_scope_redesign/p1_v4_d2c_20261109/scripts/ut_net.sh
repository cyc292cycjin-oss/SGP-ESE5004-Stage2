#!/bin/bash
# D2c section 3: the D2a network-ledger test (Fable F-05) on the D2c build (V4_D2A_BUILD points to it), plus the D2b / D2c table tests. No solver.
export V4_D2A_BUILD=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d2c/builds/main/integrated/integrated_365_24h_unsolved.nc
bash /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2c_20261109/scripts/ut.sh net_d2c tests/research/test_v4_d2a_fixes.py tests/research/test_v4_d2b_band.py tests/research/test_v4_d2b_biomass.py tests/research/test_v4_d2c_trunk.py
