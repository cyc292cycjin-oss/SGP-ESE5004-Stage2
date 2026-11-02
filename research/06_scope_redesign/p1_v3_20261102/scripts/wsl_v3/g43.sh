#!/bin/bash
W=/home/jin/wt_v3_20261102; M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
cd $W
sed -n 1,30p scripts_project/apply_selected_stock.py | cut -c1-170
grep -n "\.csv\|\.json\|\.nc\|existing_unit_components" scripts_project/apply_selected_stock.py | head -30 | cut -c1-170
grep -rn "existing_unit_components" scripts_project/*.py | head -12 | cut -c1-170
