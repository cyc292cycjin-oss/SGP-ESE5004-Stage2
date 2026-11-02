#!/bin/bash
# Supplement 05: status table of decision 180 from the identities of the bound network and GIPT 2026-09 (the source file sits in the main checkout: git-ignored), then the unit tests.
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_20261102; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W
[ -e research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv ] || ln -s $MAIN/research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv
$PY scripts_project/v3_dedicated_lines.py --network $MAIN/results_project/v3/builds_bound/integrated/integrated_2920_3h_unsolved.nc --status-table 2>&1 | grep -v -E "PROJ|Warning|warn\("
wc -l research_inputs/corridors/DEDICATED_STOCK_STATUS_V3.csv; git status --short research_inputs | head -5; git check-ignore -v research_inputs/corridors/DEDICATED_STOCK_STATUS_V3.csv research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv | cut -c1-110
bash /home/jin/v3/ut4.sh
