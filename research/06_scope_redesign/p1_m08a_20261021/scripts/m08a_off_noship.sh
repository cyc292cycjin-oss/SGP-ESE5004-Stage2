#!/bin/bash
cd /home/jin/wt_m08a_20261021/scripts_project || exit 1
/home/jin/miniforge3/envs/pypsa-earth/bin/python m08a_offshore_profiles.py --rules pypsa_eur_v2025_07_no_ship_lanes --output /home/jin/m08a_offshore_work/no_ship_lanes --work /home/jin/m08a_offshore_work \
  --no-profiles --nprocesses 4 2>&1 | grep -v -E "PROJ|Warning|warn\(" | tail -12
