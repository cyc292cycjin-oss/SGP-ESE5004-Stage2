#!/bin/bash
# S4O supplement 01: registry fragment s4o_1 (decision 121) -> DATA_REGISTRY.csv; supplement copied into the step folder; registry test
set -euo pipefail
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4o_20261019; D=research/06_scope_redesign/p1_step4o_20261019
cp -p $W/S4O_SUPPLEMENT_01.md $W/S4O_SUPPLEMENT_01_SHA256.txt $D/
sha256sum $D/S4O_SUPPLEMENT_01.md
grep -q '"s4o_0", "s4o_1"' scripts_project/d1_registry.py || sed -i 's/"s4m_0", "s4o_0"\]/"s4m_0", "s4o_0", "s4o_1"]/' scripts_project/d1_registry.py
grep -c '"s4o_1"' scripts_project/d1_registry.py
(cd scripts_project && $PY s4o_1_data.py && $PY d1_registry.py | tail -1)
git diff --stat
$PY -m pytest -q tests/research/test_d1_registry.py tests/research/test_s4o_2.py tests/research/test_s4c_5.py 2>&1 | tail -3
