#!/bin/bash
cd /home/jin/wt_v3_20261102; export PYTHONHASHSEED=0; P=/home/jin/miniforge3/envs/pypsa-earth/bin/python
$P /home/jin/v3/x1_patch3.py && $P -m pytest tests/research/test_v3.py -q --no-header -p no:cacheprovider -W ignore 2>&1 | tail -2 | cut -c1-170
bash /home/jin/v3/static2.sh 2>&1 | head -1 | cut -c1-100
cat research/06_scope_redesign/p1_v3_20261102/evidence/X1_STOCK_TABLE_V3.csv
cd scripts_project; $P /home/jin/v3/x1_load.py 2>&1 | grep -v "PROJ\|Deprecation\|fullslice" | cut -c1-130 | sed -n 2,11p
