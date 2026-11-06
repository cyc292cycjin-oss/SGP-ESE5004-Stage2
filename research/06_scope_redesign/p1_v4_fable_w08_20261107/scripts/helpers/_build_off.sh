#!/bin/bash
# Fable W08 review: build the v3.1-fallback network (every v4 switch off) with the W08 code in the temporary copy; no solver, no licence.
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
T=/home/jin/v4fable/repo; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
OUT=/home/jin/v4fable/build_off; mkdir -p $OUT $T/results_project
for d in assembly_v1 s1; do [ -e $T/results_project/$d ] || ln -s $MAIN/results_project/$d $T/results_project/$d; done
cd $T || exit 1
echo "START $(date -u +%H:%M:%S)" > $OUT/STATUS.txt
/usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/integrated > $OUT/build.log 2> $OUT/build.err
echo "BUILD exit $? $(grep -h 'Maximum resident' $OUT/build.err | tr -s ' ') $(grep -h 'Elapsed' $OUT/build.err | tr -s ' ')" >> $OUT/STATUS.txt
ls -la $OUT/integrated/ >> $OUT/STATUS.txt 2>&1
echo "DONE $(date -u +%H:%M:%S)" >> $OUT/STATUS.txt
cat $OUT/STATUS.txt; tail -5 $OUT/build.err
