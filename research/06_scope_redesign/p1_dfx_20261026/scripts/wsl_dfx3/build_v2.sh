#!/bin/bash
# DFX v3 F5.1: build the four v2 networks (integrated / disconnected; each build writes the 2920x3h network and its exact daily-mean 365x24h) with the
# same command as M08b (m08b_build.sh) at a CLEAN commit of codex/dfx-v3-20261026; no solve. Inputs through the results_project symlinks of the
# worktree (assembly_v1, s1 -> main checkout); outputs to the main checkout results_project/dfx_v3/builds_v2 (gitignored).
set -u
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=$MAIN/results_project/dfx_v3/builds_v2; mkdir -p $OUT; ST=$OUT/BUILD_STATUS.txt
cd $WT || exit 1
DIRTY=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)
[ "$DIRTY" = 0 ] || { echo "REFUSED: tracked changes under scripts_project / configs / research_inputs not committed ($DIRTY)"; exit 2; }
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse HEAD) dirty:$DIRTY" >> $ST
for t in integrated disconnected; do
  mkdir -p $OUT/$t
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $t --output $OUT/$t > $OUT/${t}_build.log 2> $OUT/${t}_build.err
  echo "BUILD_$t:$?:$(tail -1 $OUT/${t}_build.log | cut -c1-120):$(grep -h 'Maximum resident' $OUT/${t}_build.err | tr -s ' '):$(grep -h 'Elapsed' $OUT/${t}_build.err | tr -s ' ')" >> $ST
done
echo "END:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
cd $OUT && sha256sum */*_unsolved.nc >> $ST && ls -l */*_unsolved.nc >> $ST
echo DONE >> $ST
cat $ST
