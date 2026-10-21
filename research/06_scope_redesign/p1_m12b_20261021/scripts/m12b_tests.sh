#!/bin/bash
# M12b: tests. FULL=1 -> tests/research without the five toy-solve tests of earlier steps (HiGHS via PyPSA / linopy, scipy linprog);
# default -> test_m12_allocation.py + the M08a runner tests. The M12 toy LPs (scipy linprog HiGHS in test_m12_allocation.py) run (allowed by
# the M12 instruction). Gurobi is never called.
cd /home/jin/wt_m12_20261021 || exit 1
LOG=/home/jin/m12b_tests${FULL:+_full}.log
echo "start $(date -Is) head $(git rev-parse --short HEAD) dirty $(git status --porcelain --untracked-files=no | wc -l)" > $LOG
SEL="tests/research/test_m12_allocation.py tests/research/test_m08a_a8.py"
[ "${FULL:-0}" = 1 ] && SEL=tests/research
PYTHONHASHSEED=0 M12_SMOKE_DIR=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4o/s4o3/solves/s4o_integrated \
/home/jin/miniforge3/envs/pypsa-earth/bin/python -m pytest -q -p no:cacheprovider $SEL -rs \
  --deselect tests/research/test_s3b_r4.py::test_scaling_round_trip_small_model \
  --deselect tests/research/test_s4c_3.py::test_net_zero_hook_forces_non_fossil_bunkers \
  --deselect tests/research/test_s4c_5.py::test_kvl_normalisation_exact \
  --deselect tests/research/test_s4m_duals.py::test_dual_dataset_with_conflicting_dim_coords \
  --deselect tests/research/test_s4o_2.py::test_c1_kkt_terms_toy_model >> $LOG 2>&1
echo "exit=$? end $(date -Is)" >> $LOG
echo DONE >> $LOG
tail -n 25 $LOG
