#!/bin/bash
# D2c section 5: full tests/research in the D2c worktree WITHOUT any solve (instruction: at most 2 solver calls, both used in section 4). Excluded because they
# solve toy LPs: tests/research/test_m12_allocation.py (scipy linprog) and the five known toy solves (optimize / .solve / linprog). test_m10p_batch3.py only
# searches source text for "m.solve(" (kept). The network tests read the D2c build through the worktree symlinks (results_project/v4d2c, assembly_v1, s1).
set -u
R=/home/jin/wt_v4_d2c; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; LOG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2c_20261109/logs
cd $R || exit 1
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[g]urobi_cl')" = 0 ] || { echo "REFUSED: a solve is running"; exit 2; }
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
export V4_D2A_BUILD=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d2c/builds/main/integrated/integrated_365_24h_unsolved.nc
start=$(date +%s)
$PY -m pytest -q -p no:cacheprovider tests/research --ignore=tests/research/test_m12_allocation.py \
  --deselect tests/research/test_s3b_r4.py::test_scaling_round_trip_small_model \
  --deselect tests/research/test_s4c_3.py::test_net_zero_hook_forces_non_fossil_bunkers \
  --deselect tests/research/test_s4c_5.py::test_kvl_normalisation_exact \
  --deselect tests/research/test_s4m_duals.py::test_dual_dataset_with_conflicting_dim_coords \
  --deselect tests/research/test_s4o_2.py::test_c1_kkt_terms_toy_model \
  -rfE > $LOG/ut_full.txt 2>&1; rc=$?
echo "EXIT:$rc seconds:$(( $(date +%s) - start ))" >> $LOG/ut_full.txt
tail -30 $LOG/ut_full.txt
