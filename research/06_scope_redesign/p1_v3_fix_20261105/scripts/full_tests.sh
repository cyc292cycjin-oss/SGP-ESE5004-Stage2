#!/bin/bash
# full tests/research at the fix commit (no Gurobi; the toy LPs of the suite run - scipy linprog / HiGHS on toy models, no model network); not beside a real solve or dry run
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_fix; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; cd $W
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[p]ytest ')" = 0 ] || { echo "REFUSED: a solve or pytest is running"; exit 4; }
OUT=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/evidence/tests; mkdir -p $OUT; F=$OUT/FULL_SUITE_$(git rev-parse --short=8 HEAD).txt
{ echo "commit $(git rev-parse HEAD) dirty $(git status --porcelain --untracked-files=no | wc -l) start $(date -u +%FT%TZ)"
  env -u GRB_LICENSE_FILE timeout -k 60 7800 $PY -m pytest tests/research -q --no-header -p no:cacheprovider -rfE 2>&1 | grep -vE "Warning|^\s*$|warnings.warn|^  " | tail -60
  echo "end $(date -u +%FT%TZ)"; } > "$F" 2>&1
echo "FULL_SUITE_DONE $F"
