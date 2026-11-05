#!/bin/bash
# Every add_constraints call reached from install_research_constraint_hooks (constraint forms for the zero-slack check). Read-only.
set -u
cd /home/jin/wt_v3_fix/scripts_project
for f in country_carbon.py s2_layers.py carrier_architecture.py integrate_surviving_assets.py scenario_network.py s4b_candidates.py s4c_layers.py s4f_layers.py s4j_layers.py s4k_layers.py assembly_components.py; do
  echo "=================== $f"
  grep -n -E 'add_constraints|def install|def add_country_net_zero|external_annual_caps|horizon_fraction|caps_t_per_year|country_cap_tco2' "$f" | cut -c1-260
done
