#!/bin/bash
# W08 checklist section 8: intake, biomass potential v4 (compare with the I2 file), gas caps v4 (compare with W12), checkpoint S7.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106; R=/home/jin/wt_v4_w08; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
cd $W && $PY scripts/w08_intake_network.py > /home/jin/v4w08/intake_net.log 2>&1 || { cat /home/jin/v4w08/intake_net.log; exit 1; }
cd $R && $PY scripts_project/v4_biomass_potential.py || exit 1
echo "potential vs I2:"; sha256sum research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4.csv /home/jin/v4i2/BIOMASS_POTENTIAL_2050_I2.csv | cut -c1-16
$PY scripts_project/v4_gas_caps.py || exit 1
$PY - <<'EOF'
import pandas as pd
a = pd.read_csv("/home/jin/wt_v4_w08/research_inputs/gas_v5/FUGITIVE_FACTORS_V4.csv").set_index("country")
b = pd.read_csv("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/W12/tables/W12_1_FUGITIVE_FACTOR_COUPLING.csv").set_index("country")
for c in b.index:
    print(c, "factor", a.at[c, "factor_t_per_mwh"], b.at[c, "factor_marketed_basis_t_per_mwh"], "cap", a.at[c, "gas_cap_marketed_mwh"], b.at[c, "gas_cap_marketed_mwh"])
EOF
