#!/bin/bash
set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; WT=/home/jin/wt_v4_fable; T=/home/jin/v4fable; S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_fable_w08_20261107
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PKG=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks/integrated_2920_3h_unsolved.nc
OUT=$T/build_off; LOG=$T/build_off2.log; : > $LOG
echo "base_files: $(python3 -c "import json; r=json.load(open('$WT/configs/research/composition.json')); print(r['base_files'], r['identities']['integrated'])")" >> $LOG
for f in config.default.yaml config.tutorial.yaml; do cp $WT/$f $T/repo/ ; cp $WT/$f $T/tests_copy/; done
echo "== registry tests ==" >> $LOG
( cd $T/tests_copy && $PY -m pytest -q -p no:cacheprovider tests/research/test_v4_registry.py 2>&1 | tail -3 ) >> $LOG
echo "== build off ==" >> $LOG
mkdir -p $OUT $T/repo/results_project
for d in assembly_v1 s1; do [ -e $T/repo/results_project/$d ] || ln -s $MAIN/results_project/$d $T/repo/results_project/$d; done
cd $T/repo || exit 1
/usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/integrated > $OUT/build.log 2> $OUT/build.err
echo "BUILD exit $? $(grep -h 'Maximum resident' $OUT/build.err | tr -s ' ') $(grep -h 'Elapsed' $OUT/build.err | tr -s ' ')" >> $LOG
ls -la $OUT/integrated/ >> $LOG 2>&1
if [ -f $OUT/integrated/integrated_2920_3h_unsolved.nc ]; then
  echo "== compare with v3.1 package ==" >> $LOG
  $PY $S/scripts/compare_off_build.py $OUT/integrated/integrated_2920_3h_unsolved.nc $PKG $S/evidence/OFF_BUILD_VS_V31.json >> $LOG 2>&1
  python3 -c "import json; r=json.load(open('$OUT/integrated/integrated_BUILD_RECEIPT.json')); p=json.load(open('${PKG%_2920_3h_unsolved.nc}_BUILD_RECEIPT.json')); print('code_sha off', r.get('code_sha'), 'pkg', p.get('code_sha')); print('config sha off', r.get('research_config_sha256'), 'pkg', p.get('research_config_sha256'))" >> $LOG 2>&1
else
  grep -n -A12 Traceback $OUT/build.err | tail -16 >> $LOG
fi
echo "DONE $(date -u +%H:%M:%S)" >> $LOG
cat $LOG
