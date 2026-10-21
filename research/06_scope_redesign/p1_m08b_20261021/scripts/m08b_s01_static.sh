#!/bin/bash
# M08b supplement 01 section 4.2: static checks of the supplement-01 builds + comparison with the S4M-3 builds (before the corrections) and the M08b
# first-round builds (columns *_m08b1); no solve. Evidence files carry the tag S01.
set -u
WT=/home/jin/wt_m08b_20261021; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
EV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08b_20261021/evidence
cd $WT || exit 1
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
echo "head $(git rev-parse --short HEAD) dirty $(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)"
/usr/bin/time -v $PY scripts_project/m08b_static.py --repo . --new $MAIN/results_project/m08b/builds_s01 --old $MAIN/results_project/s4m/s4m3/builds \
  --prev $MAIN/results_project/m08b/builds --tag S01 --out $EV > /tmp/m08b_s01_static.log 2> /tmp/m08b_s01_static.err
echo "static exit=$?"
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
grep -v -E 'PROJ|^\s+(Page|Volun|Invol|Swaps|File sys|Socket|Signals|Exit|Average|Minor|Major|Percent|System|User|Command)' /tmp/m08b_s01_static.err | tail -15
cat /tmp/m08b_s01_static.log
