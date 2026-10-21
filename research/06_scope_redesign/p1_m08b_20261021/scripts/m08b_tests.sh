#!/bin/bash
# M08b: no-solve test subset (FILES) or the full tests/research (FULL=1); the five toy-solve tests of tests/research are always deselected
# (HiGHS via PyPSA / linopy and scipy linprog); never runs Gurobi
set -u
WT=/home/jin/wt_m08b_20261021
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
# supplement 01: the JRC-IDEES workbook is an ignored input; point the band-split sensitivity test at the main checkout copy
export M08B_IDEES_XLSX=${M08B_IDEES_XLSX:-/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/research_inputs/registry_v5/sources/jrc_idees_2021/EU27/JRC-IDEES-2021_Industry_EU27.xlsx}
cd "$WT" || exit 1
if [ "${FULL:-0}" = "1" ]; then FILES=tests/research; else FILES=${FILES:-$(ls tests/research/test_m08b_*.py)}; fi
echo "solver calls in selected files:"; grep -rn -E 'optimize\(|\.solve\(|linprog' $FILES | cut -c1-140 || echo none
LOG=${LOG:-/home/jin/m08b_tests.log}
echo "start $(date -Is) head $(git rev-parse --short HEAD) dirty $(git status --porcelain --untracked-files=no | wc -l)" > $LOG
"$PY" -m pytest -q -p no:cacheprovider $FILES -rs \
  --deselect tests/research/test_s4c_3.py::test_net_zero_hook_forces_non_fossil_bunkers \
  --deselect tests/research/test_s3b_r4.py::test_scaling_round_trip_small_model \
  --deselect tests/research/test_s4c_5.py::test_kvl_normalisation_exact \
  --deselect tests/research/test_s4m_duals.py::test_dual_dataset_with_conflicting_dim_coords \
  --deselect tests/research/test_s4o_2.py::test_c1_kkt_terms_toy_model \
  ${PYTEST_EXTRA:-} >> $LOG 2>&1
echo "exit=$? end $(date -Is)" >> $LOG
echo DONE >> $LOG
tail -${TAILN:-30} $LOG
