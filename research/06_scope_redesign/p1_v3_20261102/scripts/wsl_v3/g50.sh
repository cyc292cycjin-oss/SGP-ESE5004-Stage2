#!/bin/bash
W=/home/jin/wt_v3_20261102; cd $W
wc -l scripts_project/dfx_batch.py scripts_project/batch_def.py research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/run_dfx.sh research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/preflight_dfx.sh research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/make_package_dfx.sh
cat scripts_project/batch_def.py | cut -c1-220
echo ======; sed -n 1,80p scripts_project/dfx_batch.py | cut -c1-240
