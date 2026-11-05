#!/bin/bash
cd /home/jin/wt_v31_review || exit 1
echo "=== research_bunker_co2_limit / BUNKER_ROW / BUNKER_CO2_BUS / co2 bunkers (scripts_project, hpc_package_src, tests excluded) ==="
git grep -n -E "research_bunker_co2_limit|BUNKER_ROW|BUNKER_CO2_BUS|co2 bunkers|research_bunker_net_zero" -- scripts_project hpc_package_src | grep -v "^tests/"
echo
echo "=== consumers of nodal price tables ==="
git grep -n -E "nodal_prices|NODAL_PRICES|nodal_prices_summary" -- scripts_project hpc_package_src
echo
echo "=== python env candidates ==="
ls -d .pixi 2>/dev/null; ls /home/jin/miniforge3/envs 2>/dev/null; which python3; grep -n -E "python|conda|pixi|activate" hpc_package_src/hpr_job.sh | head -10
