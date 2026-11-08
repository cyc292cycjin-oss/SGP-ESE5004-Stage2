#!/bin/bash
# copy the git-ignored finance inputs from the main checkout into the D2c worktree (not committed; needed by test_s4c_0 only)
M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/research_inputs/finance_v5
T=/home/jin/wt_v4_d2c/research_inputs/finance_v5
ls -la $M
for f in COUNTRY_WACC_PUBLIC_SOURCES.csv DISCOUNT_RATE_IN_USE.csv; do
  if [ -e $M/$f ] && [ ! -e $T/$f ]; then cp $M/$f $T/$f && echo "copied $f"; fi
done
cd /home/jin/wt_v4_d2c && git status --short research_inputs/finance_v5
