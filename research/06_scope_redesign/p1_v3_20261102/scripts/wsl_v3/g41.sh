#!/bin/bash
# where powerplant lists live (read-only)
W=/home/jin/wt_v3_20261102; M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
cd $W
grep -rln "powerplant" scripts_project/*.py scripts_project/v5/*.py 2>/dev/null | head -12
grep -n "powerplant\|ppl\|existing_hydro\|hydro_existing\|existing_cap" configs/research/baseline.yaml | head -20
ls $M/results_project 2>/dev/null | head -40 | tr '\n' ' '
echo; find -L /home/jin/research/SGP_ESE5004_Stage2/phase2 -maxdepth 6 \( -iname 'powerplants*.csv' -o -iname '*custom_powerplants*' -o -iname '*Global-Integrated-Power*' -o -iname '*GEM*Power*' -o -iname 'ppl*.csv' \) 2>/dev/null | grep -v '/.snakemake/' | head -20
