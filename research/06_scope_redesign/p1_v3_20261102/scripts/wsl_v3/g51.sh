#!/bin/bash
R=/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/smoke_s1/integrated
head -1 $R/COUNTRY_COST_LEDGER.csv | tr ',' '\n' | tr '\n' ' ' | cut -c1-1800; echo
ls /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/smoke_s1/integrated | tr '\n' ' ' | cut -c1-900; echo
cat /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_x1b/BUILD_STATUS.txt | cut -c1-170
