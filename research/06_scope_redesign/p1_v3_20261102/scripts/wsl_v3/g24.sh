#!/bin/bash
cd /home/jin/wt_v3_20261102/scripts_project
grep -n "^LAND\|LAND *=" s4d_1_coastline.py | cut -c1-170
sed -n 139,172p s2_layers.py | cut -c1-210
sed -n 33,47p v5/gates_v6.py | cut -c1-230
sed -n 96,121p s4c_layers.py | cut -c1-190
grep -n "ASEAN\|\" oil\"\|oil non-fossil" s4b_layers.py | cut -c1-170 | head -12
grep -n "ASEAN oil\|ASEAN methanol\|ASEAN ammonia\|ASEAN_POOL" v5/*.py s2_solve.py s4l_layers.py s4j_layers.py s4k_layers.py carrier_architecture.py m08a_layers.py s4i_static_audit.py | cut -c1-170 | head -14
