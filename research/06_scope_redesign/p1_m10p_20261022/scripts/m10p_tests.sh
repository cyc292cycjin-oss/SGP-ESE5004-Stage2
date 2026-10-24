#!/bin/bash
# M10P full tests/research on the integration branch (no Gurobi; the toy LP tests (HiGHS / scipy linprog) are allowed by the M10P instruction and run)
set -u
WT=/home/jin/wt_m10p_20261022; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/evidence; TAG=${TAG:-m10p1}
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $WT || exit 1
echo "HEAD $(git rev-parse HEAD) dirty_tracked $(git status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ)" > $E/M10P_FULL_TESTS_$TAG.log
env -u GRB_LICENSE_FILE timeout 3000 $PY -m pytest tests/research -q -p no:cacheprovider -ra >> $E/M10P_FULL_TESTS_$TAG.log 2>&1
echo "EXIT $? $(date -u +%FT%TZ)" >> $E/M10P_FULL_TESTS_$TAG.log
echo DONE >> $E/M10P_FULL_TESTS_$TAG.log
