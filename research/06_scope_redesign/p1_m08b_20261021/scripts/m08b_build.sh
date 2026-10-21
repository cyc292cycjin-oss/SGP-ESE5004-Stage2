#!/bin/bash
# M08b section 3.1: rebuild integrated / disconnected (each build writes the 2920x3h network and its exact daily mean 365x24h) at the M08b code; no solve.
# Inputs from the main checkout's results_project (assembly_v1, s1) through temporary symlinks in the worktree (removed afterwards); outputs to
# the main checkout's results_project/m08b/<OUTDIR> (gitignored, not committed).
set -u
WT=/home/jin/wt_m08b_20261021; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=$MAIN/results_project/m08b/${OUTDIR:-builds}; mkdir -p $OUT; ST=$OUT/BUILD_STATUS.txt
cd $WT || exit 1
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" >> $ST
build() { local tag=$1 sc=$2; shift 2; mkdir -p $OUT/$tag
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $OUT/$tag "$@" > $OUT/${tag}_build.log 2> $OUT/${tag}_build.err
  echo "BUILD_$tag:$?:$(tail -1 $OUT/${tag}_build.log | cut -c1-120):$(grep -h 'Maximum resident' $OUT/${tag}_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/${tag}_build.err | tr -s ' ')" >> $ST; }
for t in ${TAGS:-integrated disconnected}; do build $t $t; done
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
echo "END:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
echo DONE >> $ST
