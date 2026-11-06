#!/bin/bash
# W08 section 4: build the v4 networks at the committed W08 head (no solver call, no licence): 2920x3h + 365x24h each build.
#   main/integrated   --override demand.v4.enabled=true                       (v4 main: anchors IIa, decision 211)
#   main/no_new_xb    m08a_variants.py --set cross_border.stock_mode=no_new_xb from main/integrated (2920x3h and 365x24h)
#   iid/integrated    --override demand.v4.enabled=true --override demand.anchor_mode=iid   (IId sensitivity)
# Inputs from the main checkout's results_project (assembly_v1, s1) through symlinks in the worktree (git-ignored); outputs to the main checkout's
# results_project/v4w08/builds (git-ignored).
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
W=/home/jin/wt_v4_w08; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
OUT=$MAIN/results_project/v4w08/builds; ST=$OUT/BUILD_STATUS.txt
cd $W || exit 1
DIRTY=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)
[ "$DIRTY" = 0 ] || { echo "REFUSED: tracked changes not committed ($DIRTY)"; exit 2; }
if [ -e "$ST" ] && grep -q '^DONE' "$ST"; then echo "REFUSED: $OUT holds a finished build"; exit 2; fi
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[s]2_network\.py|[g]urobi_cl')" = 0 ] || { echo "REFUSED: another solve or build is running"; exit 2; }
mkdir -p $OUT results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD)" >> $ST
build() {   # tag, overrides...
  t=$1; shift; mkdir -p $OUT/$t/integrated
  if [ -f $OUT/$t/integrated/integrated_2920_3h_unsolved.nc ] && grep -q "^BUILD_$t:0:" $ST; then echo "SKIP_$t" >> $ST; return; fi
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/$t/integrated "$@" > $OUT/${t}_integrated_build.log 2> $OUT/${t}_integrated_build.err
  echo "BUILD_$t:$?:$(grep -h 'Maximum resident' $OUT/${t}_integrated_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/${t}_integrated_build.err | tr -s ' ' | cut -c30-):$(date -u +%H:%M:%S)" >> $ST
}
build main --override demand.v4.enabled=true
for z in 2920_3h 365_24h; do
  $PY scripts_project/m08a_variants.py --repo . --base $OUT/main/integrated/integrated_${z}_unsolved.nc --out $OUT/main/no_new_xb --set cross_border.stock_mode=no_new_xb > $OUT/main_no_new_xb_$z.log 2>&1
  echo "VARIANT_main_$z:$?" >> $ST
done
build iid --override demand.v4.enabled=true --override demand.anchor_mode=iid
( cd $OUT && sha256sum */*/*_unsolved.nc ) >> $ST
ls -l $OUT/*/*/*_unsolved.nc | awk '{print $5, $9}' >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
