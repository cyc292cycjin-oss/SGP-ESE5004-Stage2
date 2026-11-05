#!/bin/bash
cd /home/jin/wt_v31_review || exit 1
export PYTHONHASHSEED=0
/home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/v31rev/store_checks2.py > /home/jin/v31rev/store_checks2.out 2> /home/jin/v31rev/store_checks2.err
echo "EXIT:$?" >> /home/jin/v31rev/store_checks2.out
