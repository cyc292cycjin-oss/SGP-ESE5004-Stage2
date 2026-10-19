#!/bin/bash
# S4O-2: unit tests of the profile / C1 changes, then the whole tests/research suite (no Gurobi: the suite never starts a Gurobi solve)
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
$PY -m pytest -q tests/research/test_s4o_2.py 2>&1 | tail -15
if [ "${1:-}" = all ]; then $PY -m pytest -q -x tests/research 2>&1 | tail -8; fi
