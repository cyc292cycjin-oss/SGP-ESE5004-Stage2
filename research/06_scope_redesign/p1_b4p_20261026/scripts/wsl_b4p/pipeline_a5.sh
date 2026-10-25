#!/bin/bash
# B4P: commits 1-3, then (sequentially, no solver anywhere) the post-processing drill, the 9-type A3.1 regression and the full test suite
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/b4p; E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026/evidence
ST=$E/PIPELINE_A5.txt; mkdir -p "$E"
log() { echo "$1:$(date -u +%FT%TZ)${2:+:$2}" >> "$ST"; }
log START
bash /home/jin/b4p/commit123.sh > "$E/commits123.log" 2>&1; log COMMITS "$(tail -5 "$E/commits123.log" | tr '\n' ' ')"
t0=$(date +%s)
WT=/home/jin/wt_b4p_20261026 bash /home/jin/wt_b4p_20261026/research/06_scope_redesign/p1_b4p_20261026/scripts/drill_b4.sh "$R/drill" > "$E/drill_b4.log" 2>&1; log DRILL "exit=$?:$(( $(date +%s) - t0 ))s:$(tail -2 "$E/drill_b4.log" | head -1 | cut -c1-400)"
cp "$R/drill/DRILL_B4.json" "$E/DRILL_B4.json" 2>/dev/null; cp "$R/drill/DRILL_STATUS.txt" "$E/DRILL_B4_STATUS.txt" 2>/dev/null
t1=$(date +%s)
bash /home/jin/b4p/regress5.sh > "$E/regress5.out" 2>&1; log REGRESS9 "exit=$?:$(( $(date +%s) - t1 ))s:$(tail -1 "$E/regress5.out")"
t2=$(date +%s)
TAG=full bash /home/jin/b4p/tests_all.sh > "$E/tests_full.out" 2>&1; log TESTS_FULL "exit=$?:$(( $(date +%s) - t2 ))s:$(tail -1 "$E/tests_full.out")"
log DONE
