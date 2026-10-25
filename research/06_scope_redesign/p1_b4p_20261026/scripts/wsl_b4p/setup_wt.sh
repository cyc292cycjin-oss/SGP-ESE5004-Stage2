#!/bin/bash
# B4P step 0: worktree inputs (git-ignored files the tests / builds need), symlinks to the main checkout's results_project
set -u
WT=/home/jin/wt_b4p_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
for f in research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv research_inputs/finance_v5/DISCOUNT_RATE_IN_USE.csv research_inputs/registry_v5/fragments/s4c_0.csv; do
  if [ -f "$MAIN/$f" ] && [ ! -f "$WT/$f" ]; then cp "$MAIN/$f" "$WT/$f" && echo "copied $f"; else echo "present or absent: $f ($([ -f "$WT/$f" ] && echo have || echo none))"; fi
done
mkdir -p "$WT/results_project"
for d in assembly_v1 s1; do [ -e "$WT/results_project/$d" ] || ln -s "$MAIN/results_project/$d" "$WT/results_project/$d"; done
ls -la "$WT/results_project"
cd "$WT" && git status --porcelain --untracked-files=no | wc -l && git rev-parse --abbrev-ref HEAD && git rev-parse HEAD
echo "== summary code"; sed -n 121,200p scripts_project/m10_batch3_summary.py
echo "== run_state"; sed -n 215,243p scripts_project/m10_batch3_summary.py
echo "== gates_v6 g2_3"; sed -n 143,165p scripts_project/v5/gates_v6.py
echo "== test counts baseline note"; ls tests/research | wc -l
