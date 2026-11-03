#!/bin/bash
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; W=/home/jin/wt_v3_hpc
cd $W; ls -la results_project | head
echo "== ignored files present in MAIN research_inputs but missing in W"
cd $MAIN
git status --porcelain --ignored=matching research_inputs configs scripts_project 2>/dev/null | awk '$1=="!!"{print $2}' > /tmp/ign_main.txt
wc -l < /tmp/ign_main.txt
n=0; while read -r p; do [ -e "$W/$p" ] || { echo "MISSING $p"; n=$((n+1)); }; done < /tmp/ign_main.txt | head -40
echo "== results_project top in MAIN"; ls $MAIN/results_project | head -60 | tr '\n' ' '
