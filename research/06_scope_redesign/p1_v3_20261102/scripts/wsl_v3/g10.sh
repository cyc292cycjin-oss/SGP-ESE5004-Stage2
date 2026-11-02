#!/bin/bash
W=/home/jin/wt_v3_20261102; cd $W
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
$PY - <<'P'
import pandas as pd
pd.set_option("display.width",200); pd.set_option("display.max_colwidth",95); pd.set_option("display.max_rows",80)
td=pd.read_csv("research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv")
x=td[td.technology.isin(["MeOH transport ship","NH3 (l) transport ship","FT fuel transport ship","CO2 (l) transport ship","Container feeder, methanol","General liquid hydrocarbon storage (product)","NH3 (l) storage tank incl. liquefaction","Ammonia transport ship"])]
print(x[["technology","parameter","value","unit","source"]].to_string())
print(sorted(t for t in td.technology.unique() if "ship" in t.lower() or "tanker" in t.lower() or "vessel" in t.lower()))
print(td[td.technology.str.contains("CO2")&td.technology.str.contains("ship|liquef",case=False)][["technology","parameter","value","unit"]].to_string()[:900])
P
echo == reg ship
grep -E "^co2_ship_chain|^co2_ship_route|^co2_extra_asean_shipping|^co2_land_transport|^conv_usd2004" research_inputs/registry_v5/DATA_REGISTRY.csv | cut -c1-300
echo == LP 2920
grep -rl "num_row\|rows" research/06_scope_redesign/p1_hpr_20261027/evidence/dry_run/BUILD_CHECK.json | head -2; cut -c1-400 research/06_scope_redesign/p1_hpr_20261027/evidence/dry_run/BUILD_CHECK.json | head -12
grep -n "2920" research/06_scope_redesign/p1_hpr_20261027/HPR_REPORT.md | grep -iE "行|列|GiB|rows|cols" | cut -c1-220 | head -6
echo == refs
cd scripts_project; grep -n "ASEAN oil\|ASEAN methanol\|ASEAN ammonia\|ASEAN_POOL" s4b_layers.py v5/v5_gates.py s4i_static_audit.py m08a_layers.py s2_network.py | cut -c1-170 | head -24
grep -n "def to_daily" -A14 daily_resolution.py | cut -c1-170 | head -26
sed -n 165,182p s4j_layers.py | cut -c1-170
