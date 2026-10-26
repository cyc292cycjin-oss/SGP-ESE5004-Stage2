#!/bin/bash
# DFX v3 amendment 2026-10-27: regenerate the reference JSON, syntax / import check, grep the old limits, run the DFX test files (no real solve running).
set -u
WT=/home/jin/wt_dfx_v3_20261026; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; export PYTHONHASHSEED=0
echo "== reference JSON"; $PY /home/jin/dfx3/make_batch3_ref.py
echo "== import / limits"; ( cd $WT && $PY scripts_project/dfx_batch.py limits && $PY -c "import sys; sys.path.insert(0, 'scripts_project'); import dfx_batch, m10_batch3_summary as m; print('m10 RUNS intact:', list(m.RUNS)[:2], len(m.RUNS))" )
echo "== old values left anywhere in the deliverable / code (expect none outside the amendment notes)"; grep -rn -E "14,646|4,269|14646|4269|15,846|5,469" $WT/scripts_project/dfx_batch.py $WT/research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx $WT/tests/research/test_dfx_runner.py | cut -c1-160
n=$(ps -eo args= | grep -E '[s]2_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '); [ "$n" = 0 ] || { echo "REAL SOLVE RUNNING"; exit 4; }
LOG=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/tests
echo "== DFX tests"; ( cd $WT && env -u GRB_LICENSE_FILE $PY -m pytest -q -p no:cacheprovider tests/research/test_dfx_runner.py tests/research/test_dfx_demand.py > $LOG/amend.log 2>&1; echo "exit=$?"; grep -E "passed|failed|^FAILED" $LOG/amend.log | tail -5 )
