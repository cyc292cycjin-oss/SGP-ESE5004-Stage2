#!/bin/bash
O=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/tests
date -u +%H:%M:%S; wc -c $O/rerun.txt; head -c 400 $O/rerun.txt; echo; tail -3 $O/rerun.txt | cut -c1-160
ps -eo pid,etimes,pcpu,args | grep -E "python.* -m pytest" | grep -v grep | cut -c1-70
ps -eo pid,etimes,pcpu,args --sort=-etimes | grep -E "pytest-of-jin" | grep -v grep | cut -c1-150 | head -6
