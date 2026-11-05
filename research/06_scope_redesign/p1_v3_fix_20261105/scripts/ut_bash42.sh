#!/bin/bash
# V3.1: the runner / job-body / submission stand-in tests with every "bash" resolved to the locally compiled bash 4.2 of the V14 session (PATH shim; no solver,
# no Gurobi, no model network). Same method as /home/jin/v3h/ut_bash42.sh (V14), plus the v3.1 package tests.
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_fix; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; S=/home/jin/v3fix/bash42_shim; B42=/home/jin/v3h/bash42/src/bash; cd $W || exit 2
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[b]4_split_solve\.py|[p]ytest ')" = 0 ] || { echo "REFUSED: a solve or pytest is running"; exit 4; }
mkdir -p $S; [ -e $S/bash ] || ln -s $B42 $S/bash
export PATH=$S:$PATH
OUT=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/evidence/tests/STANDIN_TESTS_bash42_$(git rev-parse --short=8 HEAD).txt
{ echo "commit $(git rev-parse HEAD) start $(date -u +%FT%TZ)"
  echo "bash on PATH: $(command -v bash) -> $(bash --version | head -1)"
  env -u GRB_LICENSE_FILE timeout -k 30 3600 $PY -m pytest ${@:-tests/research/test_v3_hpc_runner.py tests/research/test_hpr_two_jobs.py tests/research/test_b4p_batch4.py tests/research/test_v31_hpc_package.py} -q --no-header -p no:cacheprovider -rfE 2>&1 | tail -30
  echo "end $(date -u +%FT%TZ)"; } > "$OUT" 2>&1
cat "$OUT"
