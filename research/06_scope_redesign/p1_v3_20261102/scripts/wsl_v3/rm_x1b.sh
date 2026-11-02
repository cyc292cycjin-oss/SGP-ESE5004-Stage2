#!/bin/bash
# remove the output of the failed build attempt (own folder, only logs, first attempt stopped at the static validation)
O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_x1b
find $O -name '*.nc' | wc -l; du -sh $O | cut -f1; rm -rf $O; ls -d $O 2>/dev/null | wc -l
