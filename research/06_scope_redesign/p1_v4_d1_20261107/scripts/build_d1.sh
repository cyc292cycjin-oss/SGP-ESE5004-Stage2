#!/bin/bash
# D1 section 7.1: rebuild the v4 main networks at the committed D1 head (no solver, no licence), the W08 build rule (build_v4.sh) for the main set only:
#   main/integrated   --override demand.v4.enabled=true   (v4 main set: anchors IIa, hvc_basis b, missing_cost_rule proxy)
#   main/no_new_xb    m08a_variants.py --set cross_border.stock_mode=no_new_xb from main/integrated (2920x3h and 365x24h)
# Inputs from the main checkout's results_project (assembly_v1, s1) through symlinks in the worktree (git-ignored); outputs to the main checkout's
# results_project/v4d1/builds (git-ignored).
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
W=/home/jin/wt_v4_d1; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
OUT=$MAIN/results_project/v4d1/builds; ST=$OUT/BUILD_STATUS.txt
cd $W || exit 1
DIRTY=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)
[ "$DIRTY" = 0 ] || { echo "REFUSED: tracked changes not committed ($DIRTY)"; exit 2; }
if [ -e "$ST" ] && grep -q '^DONE' "$ST"; then echo "REFUSED: $OUT holds a finished build"; exit 2; fi
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[s]2_network\.py|[g]urobi_cl')" = 0 ] || { echo "REFUSED: another solve or build is running"; exit 2; }
mkdir -p $OUT results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD)" >> $ST
mkdir -p $OUT/main/integrated
/usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/main/integrated --override demand.v4.enabled=true > $OUT/main_integrated_build.log 2> $OUT/main_integrated_build.err
echo "BUILD_main:$?:$(grep -h 'Maximum resident' $OUT/main_integrated_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/main_integrated_build.err | tr -s ' ' | cut -c30-):$(date -u +%H:%M:%S)" >> $ST
for z in 2920_3h 365_24h; do
  $PY scripts_project/m08a_variants.py --repo . --base $OUT/main/integrated/integrated_${z}_unsolved.nc --out $OUT/main/no_new_xb --set cross_border.stock_mode=no_new_xb > $OUT/main_no_new_xb_$z.log 2>&1
  echo "VARIANT_main_$z:$?" >> $ST
done
( cd $OUT && sha256sum */*/*_unsolved.nc ) >> $ST
ls -l $OUT/*/*/*_unsolved.nc | awk '{print $5, $9}' >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
cat $ST
