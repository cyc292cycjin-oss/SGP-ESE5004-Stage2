#!/bin/bash
# M08b section 3.3-3.5: static checks of the M08b builds + comparison with the S4M-3 builds (networks before the corrections); no solve
set -u
WT=/home/jin/wt_m08b_20261021; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
EV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08b_20261021/evidence
cd $WT || exit 1
mkdir -p results_project
for d in assembly_v1 s1; do [ -e results_project/$d ] || ln -s $MAIN/results_project/$d results_project/$d; done
/usr/bin/time -v $PY scripts_project/m08b_static.py --repo . --new $MAIN/results_project/m08b/builds --old $MAIN/results_project/s4m/s4m3/builds --out $EV > /tmp/m08b_static.log 2> /tmp/m08b_static.err
echo "static exit=$?"
for d in assembly_v1 s1; do [ -L results_project/$d ] && rm results_project/$d; done
grep -v -E 'PROJ|^\s+(Page|Volun|Invol|Swaps|File sys|Socket|Signals|Exit|Average|Minor|Major|Percent|System|User|Command)' /tmp/m08b_static.err | tail -15
cat /tmp/m08b_static.log
