#!/bin/bash
# S4Q-1: script tests of the changed run pipeline on the committed HEAD (no Gurobi, no licence): (1) the S4O harness (59 checks, FIXED_RUNS off =
# unchanged S4O behaviour) with its output in the S4Q evidence folder (the S4O evidence is not touched); (2) the S4Q cases N1-N6.
set -u
W=/home/jin/wt_s4q_20261020; E=$W/research/06_scope_redesign/p1_step4q_20261020/evidence/s4q_1; PKG=$W/research/06_scope_redesign/p1_step4o_20261019/cloud_package
export PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python TMPDIR=/home/jin/s4q_tmp; mkdir -p $TMPDIR; unset GRB_LICENSE_FILE
cd $W; echo "HEAD $(git rev-parse --short=8 HEAD) dirty_code=$(git status --porcelain --untracked-files=no scripts_project configs research/06_scope_redesign/p1_step4o_20261019/cloud_package | wc -l)"
rm -rf $E/s4o4_rerun $E/results; mkdir -p $E/s4o4_rerun $E/results
bash $W/research/06_scope_redesign/p1_step4o_20261019/evidence/s4o_4/test_s4o4_scripts.sh $PKG $W $E/s4o4_rerun > $E/s4o4_rerun_stdout.txt 2>&1; echo "S4O_HARNESS_EXIT:$?"
tail -1 $E/s4o4_rerun/TEST_RESULTS.txt; grep FAIL $E/s4o4_rerun/TEST_RESULTS.txt
bash $E/test_s4q1_pipeline.sh $PKG $W $E/results > $E/results_stdout.txt 2>&1; echo "S4Q_HARNESS_EXIT:$?"
cat $E/results/TEST_RESULTS_s4q1.txt
