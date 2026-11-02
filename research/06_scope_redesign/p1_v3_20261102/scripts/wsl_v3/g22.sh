#!/bin/bash
cd /home/jin/wt_v3_20261102
du -sh research_inputs scripts_project
grep -n "class Registry" -A32 scripts_project/d1_common.py | cut -c1-170 | head -46
cut -d, -f1-3 research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv | head -3; head -1 research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv | tr ',' '\n' | grep -n ammonia
grep -E "^(ID|MY|VN)," research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv | cut -d, -f1-3
ls -d results_project 2>/dev/null; ls results_project 2>/dev/null | head -4
