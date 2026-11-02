#!/bin/bash
W=/home/jin/wt_v3_20261102; M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
ls $M/results_project/dfx_v3 | tr '\n' ' '; echo
ls $W/research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx | tr '\n' ' '; echo
sed -n 1,60p $W/research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/make_package_dfx.sh | cut -c1-200
