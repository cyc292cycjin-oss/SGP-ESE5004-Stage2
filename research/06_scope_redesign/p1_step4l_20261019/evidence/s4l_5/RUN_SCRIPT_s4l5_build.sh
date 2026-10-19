#!/bin/bash
# S4L-5 diagnostic network builds (user-authorised, 2026-10-19): S4K state (dust_cleanup off by default) with research.s2.industry.biomass_overflow_cap_share=0.98
# -> for BN, SG, VN (decision-36 rule binding) the fixed biomass demand becomes 98 % of the potential, the 2 % moves to methane by the same rule. No solve.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=results_project/s4l/s4l5; mkdir -p $OUT/builds
ST=$OUT/BUILD_STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" >> $ST
build() { local tag=$1 sc=$2; shift 2; mkdir -p $OUT/builds/$tag
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/builds/$tag --no-daily --override s2.industry.biomass_overflow_cap_share=0.98 "$@" > $OUT/builds/${tag}_build.log 2> $OUT/builds/${tag}_build.err
  echo "BUILD_$tag:$?:$(tail -1 $OUT/builds/${tag}_build.log | cut -c1-80):$(grep -h 'Maximum resident' $OUT/builds/${tag}_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/builds/${tag}_build.err | tr -s ' ')" >> $ST; }
build integrated integrated
build disconnected disconnected
(cd scripts_project && $PY s4l_5_data.py compare --s4k ../results_project/s4k/s4k3/builds --diag ../$OUT/builds --out ../research_inputs/numerics > ../$OUT/compare.log 2>&1); echo "COMPARE:$?" >> $ST
grep -v "PROJ\|FutureWarning\|warn(" $OUT/compare.log | tail -30 >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
grep -v PROJ $ST
