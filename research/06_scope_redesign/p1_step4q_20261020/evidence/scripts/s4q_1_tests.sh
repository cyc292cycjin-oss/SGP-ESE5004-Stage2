#!/bin/bash
# S4Q-1: unit tests (no Gurobi, licence variable removed) - the new test_s4q_1.py, then the whole tests/research suite, on the S4Q worktree.
set -u
W=/home/jin/wt_s4q_20261020; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W; export PYTHONHASHSEED=0; unset GRB_LICENSE_FILE
$PY -m pytest -q tests/research/test_s4q_1.py 2>&1 | tail -5
$PY -m pytest -q -p no:cacheprovider tests/research 2>&1 | tail -4
