#!/bin/bash
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3
grep -E '^(BUILD_|VARIANT|STATIC|BRIDGE|LP_|DISC_|DONE)' $R/builds_oneway/BUILD_STATUS.txt | sed -E 's/"research_constraints.*//; s/\t.*//' | cut -c1-150
grep -cE 'exit=[1-9]' $R/path_check4/STATUS.txt
grep -E '^(V6_|SCREEN|EVAL|DONE)' $R/path_check4/STATUS.txt | cut -c1-110
du -sh $R/builds_oneway | cut -f1; ls -l $R/builds_oneway/*/*_unsolved.nc | awk '{print $5, $9}' | sed 's#.*builds_oneway/##; s#^\([0-9]*\) .*builds_oneway/#\1 #'
