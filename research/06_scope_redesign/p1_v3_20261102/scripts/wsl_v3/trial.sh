#!/bin/bash
# trial build (no solve): code check only, output in results_project/v3/trial
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
mkdir -p $W/results_project; cd $W/results_project
for d in assembly_v1 s1; do [ -e $d ] || ln -s $MAIN/results_project/$d $d; done
OUT=$MAIN/results_project/v3/trial/integrated; rm -rf $OUT; mkdir -p $OUT
cd $W
/usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT --no-daily > $OUT/build.log 2> $OUT/build.err
rc=$?
echo "BUILD_EXIT=$rc"
grep -vE "Warning|warn\(|^\s+warn|PROJ:|INFO:" $OUT/build.err | grep -vE "^\s+(User|System|Percent|Average|Major|Minor|Voluntary|Involuntary|Swaps|File|Socket|Signals|Page|Exit|Command)" | tail -14 | cut -c1-260
grep -E "Elapsed|Maximum resident" $OUT/build.err | tr -s ' '
tail -1 $OUT/build.log | cut -c1-300
echo TRIAL_DONE
