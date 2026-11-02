#!/bin/bash
O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_x1b
cut -c1-250 $O/BUILD_STATUS.txt
echo ---; tail -30 $O/static.log | cut -c1-400 | head -24
echo ---; tail -24 $O/bridge.log | cut -c1-260
