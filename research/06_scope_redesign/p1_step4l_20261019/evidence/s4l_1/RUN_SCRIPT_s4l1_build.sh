#!/bin/bash
# S4L-1 builds (S4L instruction S4L-1 point 3-4, decision 113 (1)): integrated and disconnected STEPS networks with research.numerics.dust_cleanup=on
# (2920x3h only, no daily network: the S4L-2 diagnostic matrix solves 56x3h truncations), then the component-level comparison with the S4K-3 builds.
# No solve, no cloud, no download.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=results_project/s4l/s4l1; mkdir -p $OUT/builds
ST=$OUT/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" >> $ST
build() { local tag=$1 sc=$2; shift 2; mkdir -p $OUT/builds/$tag
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/builds/$tag --no-daily --override numerics.dust_cleanup=on "$@" > $OUT/builds/${tag}_build.log 2> $OUT/builds/${tag}_build.err
  echo "BUILD_$tag:$?:$(tail -1 $OUT/builds/${tag}_build.log | cut -c1-80):$(grep -h 'Maximum resident' $OUT/builds/${tag}_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/builds/${tag}_build.err | tr -s ' ')" >> $ST; }
build integrated integrated
build disconnected disconnected
(cd scripts_project && $PY s4l_1_data.py compare --s4k ../results_project/s4k/s4k3/builds --s4l ../$OUT/builds --out ../research_inputs/numerics > ../$OUT/compare.log 2>&1); echo "COMPARE:$?" >> $ST
grep -v "PROJ\|FutureWarning\|warn(" $OUT/compare.log | tail -4 >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
grep -v PROJ $ST
