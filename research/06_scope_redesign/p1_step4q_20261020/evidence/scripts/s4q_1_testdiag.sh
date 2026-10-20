#!/bin/bash
set -u
W=/home/jin/wt_s4q_20261020; M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W; export PYTHONHASHSEED=0; unset GRB_LICENSE_FILE
$PY -m pytest -q -p no:cacheprovider tests/research/test_s4c_0.py 2>&1 | grep -E "Error|No such" | head -3
f=research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv
echo "worktree has $f: $(test -e $W/$f && echo yes || echo no); main checkout: $(test -e $M/$f && echo yes || echo no); tracked: $(cd $M && git ls-files --error-unmatch $f >/dev/null 2>&1 && echo yes || echo no); ignored: $(cd $M && git check-ignore -q $f && echo yes || echo no)"
echo "== baseline 0b681881 in a temporary worktree (same env, no S4Q change)"
B=/home/jin/s4q_tmp_base; rm -rf $B; cd $M && git worktree add --detach $B 0b681881 >/dev/null 2>&1
cd $B && $PY -m pytest -q -p no:cacheprovider tests/research 2>&1 | tail -1
cd $M && git worktree remove --force $B && echo "temporary worktree removed"
