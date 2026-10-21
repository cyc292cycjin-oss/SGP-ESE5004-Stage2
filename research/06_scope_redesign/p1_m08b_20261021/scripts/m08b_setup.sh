#!/bin/bash
# M08b step 1: independent worktree + branch from the M08a head (PR #45)
set -u
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
WT=/home/jin/wt_m08b_20261021
BR=codex/m08b-demand-20261021
cd "$MAIN" || exit 1
if [ -e "$WT" ]; then echo "worktree path exists already: $WT"; exit 2; fi
git fetch -q origin codex/m08a-corrections-20261021 || exit 3
git worktree add -b "$BR" "$WT" origin/codex/m08a-corrections-20261021 || exit 4
cd "$WT" || exit 5
git log --oneline -1
git status -s | head -5
mkdir -p research_inputs/finance_v5
for f in COUNTRY_WACC_PUBLIC_SOURCES.csv DISCOUNT_RATE_IN_USE.csv; do
  [ -f research_inputs/finance_v5/$f ] || cp /home/jin/wt_m080_20261020/research_inputs/finance_v5/$f research_inputs/finance_v5/
done
ls research_inputs/finance_v5/
