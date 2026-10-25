#!/bin/bash
# B4P A5.2: the full tests/research suite on the B4P worktree (no Gurobi licence variable; the five toy HiGHS / linprog solves of the suite run as in
# M10P / M10R - disclosed in the report). Must not run beside a real local solve. TAG selects the log name.
set -u
WT=/home/jin/wt_b4p_20261026; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026/evidence/tests; TAG=${TAG:-full}
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; mkdir -p "$E"
n=$(ps -eo args= | grep -cE "[s]2_solve\.py|[b]4_split_solve\.py"); [ "$n" = 0 ] || { echo "solve process running ($n) - not started"; exit 3; }
cd "$WT" || exit 1
echo "HEAD $(git rev-parse HEAD) dirty_tracked $(git status --porcelain --untracked-files=no | wc -l) $(date -u +%FT%TZ) mode=$TAG" > "$E/TESTS_$TAG.log"
if [ "$TAG" = full ]; then
  env -u GRB_LICENSE_FILE timeout 3600 "$PY" -m pytest tests/research -q -p no:cacheprovider -ra >> "$E/TESTS_$TAG.log" 2>&1
else
  env -u GRB_LICENSE_FILE timeout 2400 "$PY" -m pytest tests/research/test_b4p_split.py tests/research/test_b4p_batch4.py tests/research/test_b4p_paths.py tests/research/test_b4p_install_env.py -q -p no:cacheprovider -ra >> "$E/TESTS_$TAG.log" 2>&1
fi
echo "EXIT $? $(date -u +%FT%TZ)" >> "$E/TESTS_$TAG.log"; tail -3 "$E/TESTS_$TAG.log"
