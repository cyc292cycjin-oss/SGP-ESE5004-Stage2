#!/bin/bash
W=/home/jin/wt_v3_20261102; cd $W
wc -l scripts_project/v3_data.py; tail -22 scripts_project/v3_data.py | cut -c1-240
grep -n "def add" -A6 scripts_project/d1_common.py | head -24 | cut -c1-200
git check-ignore -v research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv research_inputs/corridors/CORRIDOR_APG_CROSSCHECK_2024.csv | cut -c1-140
git ls-files research_inputs/corridors | wc -l; git status --short | head -10 | cut -c1-100
