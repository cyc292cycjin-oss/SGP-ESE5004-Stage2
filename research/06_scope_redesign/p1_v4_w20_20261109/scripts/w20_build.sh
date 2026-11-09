#!/bin/bash
# V4 W20 section 2 (V4_W20_INSTRUCTION.md SHA f4419a83): the 17 coalition networks (decision 228), built from the W14 v4 main integrated 2920x3h network
# with scripts_project/v4_coalition.py and cut to 56 snapshots by the s2_solve.py --truncate rule. No solver.
set -u
WT=/home/jin/wt_v4_w20; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
BASE=$MAIN/results_project/v4w14/builds/main/integrated/integrated_2920_3h_unsolved.nc
OUT=$MAIN/results_project/v4w20/nets56; mkdir -p $OUT
cd $WT || exit 1
echo "START $(date -u +%FT%TZ) commit=$(git rev-parse HEAD) dirty=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l) base_sha=$(sha256sum $BASE | cut -c1-64)"
for c in $($PY scripts_project/v4_coalition.py list | cut -d' ' -f1); do
  $PY scripts_project/v4_coalition.py build --base $BASE --coalition $c --out $OUT --truncate 56 --expect-base-sha256 86f6d6a0fce2f0e0 > $OUT/${c}_build.log 2>&1
  echo "$c exit=$? $(sha256sum $OUT/${c}_56_unsolved.nc | cut -c1-64) $(stat -c %s $OUT/${c}_56_unsolved.nc)"
done
echo "DONE $(date -u +%FT%TZ)"
