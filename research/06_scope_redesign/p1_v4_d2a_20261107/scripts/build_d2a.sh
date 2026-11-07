#!/bin/bash
# D2a section 5 (and 7): rebuild the v4 networks at the committed D2a head (no solver, no licence), the W08 / D1 build rule:
#   <set>/integrated   s2_network.py --scenario integrated --override demand.v4.enabled=true [--override demand.v4.<key>=<value> ...]
#   <set>/no_new_xb    m08a_variants.py --set cross_border.stock_mode=no_new_xb from <set>/integrated (2920x3h and 365x24h)
# usage: build_d2a.sh <set name: main | d4p31 | d31p4 | phs_asean> [extra --override k=v ...]
# Inputs from the main checkout's results_project (assembly_v1, s1) through symlinks in the worktree (git-ignored); outputs to the main checkout's
# results_project/v4d2a/builds/<set> (git-ignored; a symlink results_project/v4d2a in the worktree points there for the tests).
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
W=/home/jin/wt_v4_d2a; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
SET=${1:?set name}; shift
OUT=$MAIN/results_project/v4d2a/builds/$SET; ST=$OUT/BUILD_STATUS.txt
cd $W || exit 1
DIRTY=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)
[ "$DIRTY" = 0 ] || { echo "REFUSED: tracked changes not committed ($DIRTY)"; exit 2; }
if [ -e "$ST" ] && grep -q '^DONE' "$ST"; then echo "REFUSED: $OUT holds a finished build"; exit 2; fi
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[s]2_network\.py|[g]urobi_cl')" = 0 ] || { echo "REFUSED: another solve or build is running"; exit 2; }
mkdir -p $OUT/integrated results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
[ -e results_project/v4d2a ] || ln -s $MAIN/results_project/v4d2a results_project/v4d2a
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD) set:$SET overrides:$*" >> $ST
OV=(--override demand.v4.enabled=true); for o in "$@"; do OV+=(--override "$o"); done
/usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/integrated "${OV[@]}" > $OUT/integrated_build.log 2> $OUT/integrated_build.err
echo "BUILD_integrated:$?:$(grep -h 'Maximum resident' $OUT/integrated_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/integrated_build.err | tr -s ' ' | cut -c30-):$(date -u +%H:%M:%S)" >> $ST
for z in 2920_3h 365_24h; do
  $PY scripts_project/m08a_variants.py --repo . --base $OUT/integrated/integrated_${z}_unsolved.nc --out $OUT/no_new_xb --set cross_border.stock_mode=no_new_xb > $OUT/no_new_xb_$z.log 2>&1
  echo "VARIANT_no_new_xb_$z:$?" >> $ST
done
( cd $OUT && sha256sum */*_unsolved.nc ) >> $ST
ls -l $OUT/*/*_unsolved.nc | awk '{print $5, $9}' >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
cat $ST
