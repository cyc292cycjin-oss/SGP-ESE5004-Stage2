#!/bin/bash
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
du -sh $R/results_project/v3 $R/results_project/v3/intake $R/results_project/v3/intake/* $R/results_project/v3/phase1 /home/jin/wt_v3_20261102 /home/jin/v3 2>/dev/null
ps -eo pid,cmd | grep -E '[g]urobi|[s]2_solve' || echo no-solver
cd /home/jin/wt_v3_20261102 && git status --short | head
