#!/bin/bash
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; W=/home/jin/wt_v3_20261102
echo "== demand table generator"; grep -ln "DEMAND_BY_COUNTRY_SECTOR_CARRIER" $W/scripts_project/*.py $W/research/06_scope_redesign/p1_dfx_20261026/scripts/*/* 2>/dev/null | head
echo "== data chain"; cat /home/jin/dfx3/data_chain.sh 2>/dev/null | cut -c1-170 | head -40
echo "== build"; cat /home/jin/dfx3/build_v2.sh 2>/dev/null | cut -c1-200 | head -30
echo "== ignored inputs worktree"; cd $W; for f in research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv research_inputs/renewable_v5/regions_onshore.geojson research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv research_inputs/assembly_v1/sources/industry_cache.json; do [ -e $f ] && echo "ok  $f" || echo "MISSING $f"; done
echo "== fleet data"; find /home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources -iname '*transport*' 2>/dev/null | head; grep -rl "number cars" /home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources 2>/dev/null | head -5
head -c 400 research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv; echo
grep -nE "Battery electric|passenger" research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv | cut -c1-150 | head -12
