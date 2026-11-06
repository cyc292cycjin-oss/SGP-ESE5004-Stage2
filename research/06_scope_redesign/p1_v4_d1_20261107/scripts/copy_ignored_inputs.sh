#!/bin/bash
# D1: git-ignored inputs that a fresh worktree lacks (memory note: tests/research baseline), copied from the main checkout (not committed).
set -u
R=/home/jin/wt_v4_d1; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
for f in COUNTRY_WACC_PUBLIC_SOURCES.csv DISCOUNT_RATE_IN_USE.csv; do
  [ -e $R/research_inputs/finance_v5/$f ] || cp $MAIN/research_inputs/finance_v5/$f $R/research_inputs/finance_v5/$f && echo "copied $f"
done
cd $R && git status --short --ignored=matching research_inputs/finance_v5
