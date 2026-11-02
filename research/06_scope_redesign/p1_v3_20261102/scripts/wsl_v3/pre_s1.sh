#!/bin/bash
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3
echo "nproc=$(nproc)"; free -m | sed -n 2,3p
grep -E '^END_' $R/smoke_r2/STATUS.txt | cut -c1-130
ls $R/smoke_s1 2>/dev/null | head
date -u +%Y-%m-%dT%H:%MZ
