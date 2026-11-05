#!/bin/bash
# List every code usage of the bunker row name / constant (instruction 2.3). Read-only.
set -u
cd /home/jin/wt_v3_fix
echo "== git grep (all tracked files except research/ docs)"
git grep -n -E 'BUNKER_ROW|research_bunker_co2_limit|bunker_co2_limit|BUNKER_CO2_BUS|research_bunker_net_zero|install_bunker_net_zero|validate_bunker_account|B1_BUNKERS|bunkers ASEAN' -- . ':!research/' | cut -c1-260
