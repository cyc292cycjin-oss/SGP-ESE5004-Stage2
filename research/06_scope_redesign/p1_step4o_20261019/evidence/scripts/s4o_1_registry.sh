#!/bin/bash
# S4O-1.3: registry fragment s4o_0 (decisions 118-120) -> DATA_REGISTRY.csv; registry test
set -euo pipefail
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
(cd scripts_project && $PY s4o_0_data.py && $PY d1_registry.py | tail -2)
git diff --stat
$PY -m pytest -q tests/research/test_d1_registry.py 2>&1 | tail -3
