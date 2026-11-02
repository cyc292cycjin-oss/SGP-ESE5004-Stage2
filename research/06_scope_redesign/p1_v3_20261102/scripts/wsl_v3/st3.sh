#!/bin/bash
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/smoke
date -u +%H:%M:%S; cut -c1-200 $R/STATUS.txt 2>/dev/null | tail -24
ps -eo etimes,rss,pcpu,args | grep -E "python.*[s]2_solve" | grep -v "time -v" | cut -c1-60
for s in integrated no_new_xb; do f=$R/$s/gurobi.linopy.log; [ -f $f ] && { echo "--$s"; grep -E "^Barrier|Fingerprint|Optimize a model|Presolved:|Solved in|Optimal objective" $f | cut -c1-110 | sed -E 's/(Academic|WLS|license).*//' | tail -5; tail -1 $f | cut -c1-90; }; done
