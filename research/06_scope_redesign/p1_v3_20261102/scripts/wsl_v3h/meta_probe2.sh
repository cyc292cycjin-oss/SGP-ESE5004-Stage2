#!/bin/bash
PY=$HOME/miniforge3/envs/pypsa-earth/bin/python
B=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_op
$PY /home/jin/v3h/meta_probe2.py $B/integrated/integrated_2920_3h_unsolved.nc
cd /home/jin/wt_v3_hpc
grep -n "DIRECT" scripts_project/s4d_ledger.py | head -5; grep -n "DIRECT" scripts_project/m12_allocation.py | head -5
grep -n "def gate_b1_country_net_zero" -A 14 scripts_project/v5/v5_gates.py
sed -n 190,205p scripts_project/s4d_ledger.py
grep -n "liquid_ship_ckm_td\|liquid_ship_fixed_ieaghg\|liquid_ship_ckm_ieaghg\|liquid_ship_cargo" research_inputs/registry_v5/fragments/v3.csv | cut -c1-400
head -1 research_inputs/registry_v5/fragments/v3.csv
cat research/06_scope_redesign/p1_v3_20261102/scripts/wsl_v3d/build_s7.sh
