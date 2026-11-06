#!/bin/bash
# W08 checklist section 3: frozen v3 anchor tables (IId / IIb) from the v3.1 m08b run; dump compared with the reference engine's anchors_v3_ras.json.
set -u
R=/home/jin/wt_v4_w08; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
cd $R || exit 1
$PY scripts_project/v4_industry.py --write-anchor-tables --work /home/jin/v4w08/work_anchor || exit 1
$PY - <<'EOF'
import json
a = json.load(open("/home/jin/wt_v4_w08/research_inputs/industry_v4/ANCHORS_V31_RAS_DUMP.json"))
b = json.load(open("/home/jin/v4w08/ref_main/anchors_v3_ras.json"))
print("dump == reference anchors_v3_ras.json:", a == b)
EOF
git status --short | head
