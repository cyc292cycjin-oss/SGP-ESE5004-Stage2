#!/bin/bash
# V3 supplement 07: full tests/research on the packaged commit (toy solves are HiGHS / scipy linprog; Gurobi licence path set to a missing file); refuses while a solve or pytest is running.
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj GRB_LICENSE_FILE=/nonexistent
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/tests
cd $W || exit 1
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[p]ytest')" = 0 ] || { echo "REFUSED: another solve or pytest is running"; exit 2; }
echo "commit $(git rev-parse --short HEAD) tracked changes $(git status --porcelain --untracked-files=no | wc -l) start $(date -u +%H:%M:%S)" > $O/full_s7.txt
timeout -k 30 3000 $PY -m pytest tests/research -q --no-header -p no:cacheprovider --tb=line -W ignore >> $O/full_s7.txt 2>&1
echo "exit=$? end $(date -u +%H:%M:%S)" >> $O/full_s7.txt
head -1 $O/full_s7.txt; grep -E "^FAILED|^ERROR|passed|failed" $O/full_s7.txt | cut -c1-200 | tail -12
