#!/bin/bash
# full tests/research at the package commit (no Gurobi; the toy LPs of the suite run - scipy linprog / HiGHS on toy models, no model network); not beside a real solve or dry run
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_hpc; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; cd $W
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py')" = 0 ] || { echo "REFUSED: a solve is running"; exit 4; }
echo "commit $(git rev-parse HEAD) dirty $(git status --porcelain --untracked-files=no | wc -l) start $(date -u +%FT%TZ)"
env -u GRB_LICENSE_FILE timeout -k 60 7800 $PY -m pytest tests/research -q --no-header -p no:cacheprovider -rf 2>&1 | grep -vE "Warning|^\s*$|warnings.warn|^  " | tail -40
echo "end $(date -u +%FT%TZ)"
