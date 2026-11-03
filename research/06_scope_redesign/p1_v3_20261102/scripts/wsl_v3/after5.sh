#!/bin/bash
# V3 supplement 05 section 2 item 6 and tests, serial: dry run of the screening runner, package with preflight, the tests that touch the changed code (no solver, no licence, no cloud). The full suite (28 min) would pass the 1.5 h cap of the review.
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; cd /home/jin/v3
date -u +DRY_START:%H:%M:%S; bash dry_s5.sh > /home/jin/v3/out_dry5.txt 2>&1; echo "DRY_EXIT:$?"; tail -8 /home/jin/v3/out_dry5.txt | cut -c1-230
date -u +PKG_START:%H:%M:%S; bash pkg_s5.sh > /home/jin/v3/out_pkg5.txt 2>&1; echo "PKG_EXIT:$?"; tail -34 /home/jin/v3/out_pkg5.txt | cut -c1-210
date -u +TEST_START:%H:%M:%S; cd $W; echo "commit $(git rev-parse --short HEAD) real solves $(ps -eo args= | grep -cE '[s]2_solve\.py')" > /home/jin/v3/out_tests5.txt
T=tests/research; env -u GRB_LICENSE_FILE timeout -k 30 1200 $PY -m pytest $T/test_v3.py $T/test_v3_runners.py $T/test_s4d_3.py $T/test_s4d_4.py $T/test_s4d_6.py $T/test_s4b_1.py $T/test_s4a_fleet.py $T/test_dfx_runner.py $T/test_dfx_demand.py $T/test_m08a_a3.py $T/test_m08a_a7.py $T/test_m08b_s01.py $T/test_m10r_keepstock_ledger.py $T/test_b4p_batch4.py $T/test_gate4_activation.py $T/test_surviving_asset_integration.py -q --no-header -p no:cacheprovider --tb=line -W ignore >> /home/jin/v3/out_tests5.txt 2>&1
echo "TESTS_EXIT:$?"; tail -9 /home/jin/v3/out_tests5.txt | cut -c1-190; date -u +END:%H:%M:%S
