#!/bin/bash
cd /home/jin/wt_m08a_20261021/scripts_project || exit 1
LOG=/home/jin/m08a_offshore_work/full_run.log
echo "start $(date -Is)" > $LOG
/usr/bin/time -v /home/jin/miniforge3/envs/pypsa-earth/bin/python m08a_offshore_profiles.py --output /home/jin/wt_m08a_20261021/research_inputs/renewable_v5/offshore_m08a \
  --work /home/jin/m08a_offshore_work --nprocesses 4 >> $LOG 2>&1
echo "exit=$? end $(date -Is)" >> $LOG
echo DONE >> $LOG
