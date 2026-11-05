#!/bin/bash
cd /home/jin/wt_v31_review || exit 1
export PYTHONHASHSEED=0
/home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/v31rev/net_checks.py > /home/jin/v31rev/net_checks.out 2> /home/jin/v31rev/net_checks.err
echo "EXIT:$?" >> /home/jin/v31rev/net_checks.out
