#!/bin/bash
# M10R B4.1: the full tests/research once (toy LP tests allowed by the baseline 615 passed / 68 skipped of M10A; GRB_LICENSE_FILE removed; no Gurobi).
# The M10R real-data tests run against the local 56x3h keep-stock solve and the drill record. Must NOT run while a real s2_solve.py / BUILD_ONLY dry run runs.
set -u
WT=/home/jin/wt_m10p_20261022; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10r_20261024/evidence/tests; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m10r
mkdir -p $E; cd $WT || exit 1
[ "$(ps -eo args= | grep -E '[s]2_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env ')" = 0 ] || { echo "solver / build process running - not started"; exit 3; }
L=$E/TESTS_full.log
echo "HEAD $(git rev-parse HEAD) dirty_tracked $(git status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ) mode=full" > $L
env -u GRB_LICENSE_FILE PYTHONHASHSEED=0 M10R_KEEPSTOCK_DIR=$M/keepstock_v5 M10R_DRILL_JSON=$M/drill/DRILL_POSTPROC.json timeout 3600 $PY -m pytest tests/research -q -p no:cacheprovider -ra >> $L 2>&1; echo "EXIT $?" >> $L
echo "END $(date -u +%FT%TZ)" >> $L; echo DONE >> $L
grep -E "^(EXIT|HEAD|END|FAILED|ERROR)|passed|failed|error" $L | tail -12
