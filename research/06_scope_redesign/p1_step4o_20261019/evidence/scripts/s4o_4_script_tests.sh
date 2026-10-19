#!/bin/bash
# S4O-4 point 3: script tests of the S4O package scripts (no Gurobi, no licence): run_365x24h.sh + preflight.sh harness and the speed-probe harness
# (S4O copy with the decision-121 cap base). TMPDIR on the WSL disk (preflight disk check needs >= 35 GiB).
set -u
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
E=$RM/research/06_scope_redesign/p1_step4o_20261019/evidence/s4o_4; PKG=${1:-$RM/research/06_scope_redesign/p1_step4o_20261019/cloud_package}
export PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python TMPDIR=/home/jin/s4o_tmp; mkdir -p $TMPDIR
rm -rf $E/results; mkdir -p $E/results
bash $E/test_s4o4_scripts.sh $PKG $RM $E/results > $E/results_stdout.txt 2>&1; echo "SCRIPTS_EXIT:$?"
tail -1 $E/results/TEST_RESULTS.txt; grep FAIL $E/results/TEST_RESULTS.txt
bash $E/test_s4o4_probe.sh $PKG $E/results > $E/results_probe_stdout.txt 2>&1; echo "PROBE_EXIT:$?"
tail -1 $E/results/TEST_RESULTS_probe.txt; grep FAIL $E/results/TEST_RESULTS_probe.txt
exit 0
