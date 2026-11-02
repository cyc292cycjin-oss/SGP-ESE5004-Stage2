#!/bin/bash
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3
du -sm $R/builds_x1b $R/path_check3 $R/smoke_s2 $R/dry_screen $R/pkg_check | awk '{s+=$1; print $1, $2} END {print s, "MB total"}' | sed 's#/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/##'
cp $R/dry_screen/DRY_RUN_SCREEN.json /home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/
