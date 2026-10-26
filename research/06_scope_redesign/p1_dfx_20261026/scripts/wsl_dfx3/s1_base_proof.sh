#!/bin/bash
# DFX v3: is the S1 static-validation failure pre-existing at the base commit 55ab07c0? Temporary detached worktree + the same results_project/s1 link,
# run the one test file, then remove the temporary worktree (nothing of the repository is changed).
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/dfx3/wt_base_check
export PYTHONHASHSEED=0
cd $WT || exit 1
git worktree add -q --detach $T 55ab07c0 || exit 1
mkdir -p $T/results_project && ln -s $MAIN/results_project/s1 $T/results_project/s1
( cd $T && env -u GRB_LICENSE_FILE $PY -m pytest -q -p no:cacheprovider tests/research/test_s1_built_networks.py 2>&1 | grep -E "passed|failed|ValueError:" | tail -3 )
echo "base config has stock_mode: $(grep -c "stock_mode" $T/configs/research/baseline.yaml)"; git -C $T log --oneline -1
cd $WT && git worktree remove --force $T && echo "temporary worktree removed"; git worktree list | head -5
