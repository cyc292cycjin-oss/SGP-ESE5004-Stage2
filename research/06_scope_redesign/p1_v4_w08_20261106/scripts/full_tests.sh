#!/bin/bash
# W08 acceptance A3: full tests/research at the W08 head, the five toy-solve tests deselected (the instruction authorises only the four section-5
# solves). Any other file with optimize( / .solve( / linprog stops the run. Ignored finance inputs copied from the main checkout (memory note).
set -u
R=/home/jin/wt_v4_w08; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
LOG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106/logs; mkdir -p $LOG
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
cd $R || exit 1
for f in COUNTRY_WACC_PUBLIC_SOURCES.csv DISCOUNT_RATE_IN_USE.csv; do [ -e research_inputs/finance_v5/$f ] || cp $MAIN/research_inputs/finance_v5/$f research_inputs/finance_v5/$f 2>/dev/null; done
# test_m10p_batch3.py only matches as a source string (src.index("status, condition = m.solve(") of the runner check): allowed, not deselected.
KNOWN="tests/research/test_m10p_batch3.py tests/research/test_s3b_r4.py tests/research/test_s4c_3.py tests/research/test_s4c_5.py tests/research/test_s4m_duals.py tests/research/test_s4o_2.py tests/research/test_m12_allocation.py"
OTHER=$(grep -lE 'optimize\(|\.solve\(|linprog' tests/research/*.py | grep -vxF -f <(echo $KNOWN | tr ' ' '\n'))
[ -z "$OTHER" ] || { echo "REFUSED: other solving test files: $OTHER"; exit 4; }
$PY -m pytest -q -p no:cacheprovider tests/research \
  --deselect tests/research/test_s3b_r4.py::test_scaling_round_trip_small_model \
  --deselect tests/research/test_s4c_3.py::test_net_zero_hook_forces_non_fossil_bunkers \
  --deselect tests/research/test_s4c_5.py::test_kvl_normalisation_exact \
  --deselect tests/research/test_s4m_duals.py::test_dual_dataset_with_conflicting_dim_coords \
  --deselect tests/research/test_s4o_2.py::test_c1_kkt_terms_toy_model \
  --deselect tests/research/test_m12_allocation.py::test_toy_kvl_loop_dual_form_in_core_market_minus_dual_is_loop_transfer \
  --deselect tests/research/test_m12_allocation.py::test_toy_owen_in_core_identity_and_market_form \
  --deselect tests/research/test_m12_allocation.py::test_toy_bunker_player_within_strict_standalone_cost \
  --deselect tests/research/test_m12_allocation.py::test_toy_alpha_changes_no_total_and_interval \
  --deselect tests/research/test_m12_allocation.py::test_toy_dual_degeneracy_every_alpha_in_core \
  --deselect tests/research/test_m12_allocation.py::test_toy_shared_rhs_breaks_attribution_until_assigned > $LOG/full_tests.txt 2>&1
echo "EXIT:$?" >> $LOG/full_tests.txt
tail -3 $LOG/full_tests.txt
