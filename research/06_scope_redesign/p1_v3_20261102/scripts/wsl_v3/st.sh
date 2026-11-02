#!/bin/bash
M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3
date -u +%H:%M:%S
cut -c1-170 $M/path_check2/STATUS.txt 2>/dev/null | tail -24
tail -3 $M/tests/full.txt 2>/dev/null | cut -c1-160
ps -eo etimes,args | grep -E "[s]2_solve|[p]ytest " | grep -v "time -v\|timeout" | cut -c1-90 | head -3
