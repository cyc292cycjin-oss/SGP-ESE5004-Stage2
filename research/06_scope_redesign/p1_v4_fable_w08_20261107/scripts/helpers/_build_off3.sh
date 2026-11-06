#!/bin/bash
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4fable; S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_fable_w08_20261107
PKG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks/integrated_2920_3h_unsolved.nc
OUT=$T/build_off; LOG=$T/build_off3.log; : > $LOG
cd $T/repo || exit 1
if [ ! -d .git ]; then
  git init -q . && git add -A . > /dev/null 2>&1 && git -c user.name=fable-review -c user.email=review@local commit -qm "snapshot of the W08 head copy for the fallback build (not the project history)" && echo "snapshot commit $(git rev-parse HEAD)" >> $LOG
fi
rm -rf $OUT/integrated; mkdir -p $OUT/integrated
/usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/integrated > $OUT/build.log 2> $OUT/build.err
echo "BUILD exit $? $(grep -h 'Maximum resident' $OUT/build.err | tr -s ' ') $(grep -h 'Elapsed' $OUT/build.err | tr -s ' ')" >> $LOG
ls -la $OUT/integrated/*.nc >> $LOG 2>&1
if [ -f $OUT/integrated/integrated_2920_3h_unsolved.nc ]; then
  sha256sum $OUT/integrated/integrated_2920_3h_unsolved.nc $PKG >> $LOG
  $PY $S/scripts/compare_off_build.py $OUT/integrated/integrated_2920_3h_unsolved.nc $PKG $S/evidence/OFF_BUILD_VS_V31.json >> $LOG 2>&1
  python3 -c "import json; r=json.load(open('$OUT/integrated/integrated_BUILD_RECEIPT.json')); p=json.load(open('${PKG%_2920_3h_unsolved.nc}_BUILD_RECEIPT.json')); print('code_sha off', r.get('code_sha'), 'pkg', p.get('code_sha')); print('config sha off', r.get('research_config_sha256'), 'pkg', p.get('research_config_sha256')); print('subset sha off', r.get('research_config_subset_sha256'), 'pkg', p.get('research_config_subset_sha256'))" >> $LOG 2>&1
else
  grep -n -A12 Traceback $OUT/build.err | tail -16 >> $LOG
fi
echo "DONE $(date -u +%H:%M:%S)" >> $LOG
cat $LOG
