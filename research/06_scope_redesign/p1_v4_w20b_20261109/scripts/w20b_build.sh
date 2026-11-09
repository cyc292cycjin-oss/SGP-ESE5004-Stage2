#!/bin/bash
# V4 W20b section 2.4 (V4_W20B_INSTRUCTION.md SHA 25f1db61; decision 230): the 18 networks - R0 (all 11 countries, no bunker) and the 17 merged-game
# coalitions with include_bunker="ports" - built from the W14 v4 main integrated 2920x3h network with scripts_project/v4_coalition.py
# (--w20b-run) and cut to 56 snapshots by the s2_solve.py --truncate rule. No solver.
set -u
WT=/home/jin/wt_v4_w20b; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
BASE=$MAIN/results_project/v4w14/builds/main/integrated/integrated_2920_3h_unsolved.nc
OUT=$MAIN/results_project/v4w20b/nets56; mkdir -p $OUT
cd $WT || exit 1
echo "START $(date -u +%FT%TZ) commit=$(git rev-parse HEAD) dirty_tracked=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l) module_sha256=$(sha256sum scripts_project/v4_coalition.py | cut -c1-64) base_sha=$(sha256sum $BASE | cut -c1-64)"
$PY scripts_project/v4_coalition.py list --w20b | while read -r run net mode members; do
  $PY scripts_project/v4_coalition.py build --base $BASE --w20b-run $run --out $OUT --truncate 56 --expect-base-sha256 86f6d6a0fce2f0e0 > $OUT/${run}_build.log 2>&1
  echo "$run $net $mode exit=$? $(sha256sum $OUT/${net}_56_unsolved.nc | cut -c1-64) $(stat -c %s $OUT/${net}_56_unsolved.nc)"
done
echo "DONE $(date -u +%FT%TZ)"
