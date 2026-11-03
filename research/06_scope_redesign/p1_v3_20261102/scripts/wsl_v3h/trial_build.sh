#!/bin/bash
# trial: rebuild the integrated network at 5e372e5d in the new worktree (no config change) -> compare with the registered 1bddacb7 (path effect only); no solver
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj
W=/home/jin/wt_v3_hpc; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
OUT=$MAIN/results_project/v3hpc/trial_5e372e5d; ST=$OUT/STATUS.txt
cd $W; [ "$(git rev-parse HEAD)" = 5e372e5d64b0a1fe5ba45ad3d3cfa5f6b0f5a3b7 ] || git log -1 --format=%H
[ ! -e $OUT ] || { echo "REFUSED: $OUT exists"; exit 2; }
mkdir -p $OUT/integrated
echo "START:$(date -u +%FT%TZ):commit=$(git rev-parse HEAD):dirty=$(git status --porcelain --untracked-files=no | wc -l)" > $ST
/usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/integrated > $OUT/integrated_build.log 2> $OUT/integrated_build.err
echo "BUILD:$?:$(grep -h 'Maximum resident' $OUT/integrated_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/integrated_build.err | tr -s ' ' | cut -c30-)" >> $ST
( cd $OUT && sha256sum */*_unsolved.nc ) >> $ST
echo "DONE:$(date -u +%FT%TZ)" >> $ST
cat $ST
