#!/bin/bash
# W14 section 2.1: build the v4 main networks (no solver, no licence) at the committed W14 head - the D2c / D2b / W08 / D1 build rule unchanged:
#   <set>/integrated   s2_network.py --scenario integrated --override demand.v4.enabled=true   (v4 main switch set = the configuration defaults)
#   <set>/no_new_xb    m08a_variants.py --set cross_border.stock_mode=no_new_xb from <set>/integrated (2920x3h and 365x24h)
# usage: build_w14.sh <set name: main | rebuild_pkg>
#   main         the package networks (build commit registered in BATCH_DEF.json build_commit; their build receipts go into the package)
#   rebuild_pkg  the verification rebuild at the package commit (same worktree path, so the files must be byte-identical to main)
# The 2920x3h networks are only built (no LP here; the HPC builds the LP). PYTHONHASHSEED=0 (deterministic NetCDF). Inputs from the main checkout's
# results_project (assembly_v1, s1) through symlinks in the worktree (git-ignored); outputs to the main checkout's results_project/v4w14/builds/<set>.
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
W=/home/jin/wt_v4_w14; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
SET=${1:?set name}
OUT=$MAIN/results_project/v4w14/builds/$SET; ST=$OUT/BUILD_STATUS.txt
cd $W || exit 1
DIRTY=$(git status --porcelain --untracked-files=no | wc -l)
[ "$DIRTY" = 0 ] || { echo "REFUSED: tracked changes not committed ($DIRTY)"; exit 2; }
[ ! -e "$OUT" ] || { echo "REFUSED: $OUT exists (a build folder is never reused)"; exit 2; }
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[s]2_network\.py|[g]urobi_cl|[b]4_split_solve\.py')" = 0 ] || { echo "REFUSED: another solve or build is running"; exit 2; }
mkdir -p $OUT/integrated results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
[ -e results_project/v4w14 ] || ln -s $MAIN/results_project/v4w14 results_project/v4w14
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD) set:$SET overrides:demand.v4.enabled=true" >> $ST
/usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/integrated --override demand.v4.enabled=true > $OUT/integrated_build.log 2> $OUT/integrated_build.err
echo "BUILD_integrated:$?:$(grep -h 'Maximum resident' $OUT/integrated_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/integrated_build.err | tr -s ' ' | cut -c30-):$(date -u +%H:%M:%S)" >> $ST
for z in 2920_3h 365_24h; do
  $PY scripts_project/m08a_variants.py --repo . --base $OUT/integrated/integrated_${z}_unsolved.nc --out $OUT/no_new_xb --set cross_border.stock_mode=no_new_xb > $OUT/no_new_xb_$z.log 2>&1
  echo "VARIANT_no_new_xb_$z:$?" >> $ST
done
( cd $OUT && sha256sum */*_unsolved.nc ) >> $ST
ls -l $OUT/*/*_unsolved.nc | awk '{print $5, $9}' >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
cat $ST
