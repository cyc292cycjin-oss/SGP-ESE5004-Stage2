#!/bin/bash
cd /home/jin/wt_v3_20261102
C=research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml
grep -nE "land_transport|bev_|v2g|V2G|EV_|transport_electric|transport_fuel_cell|transport_ice|agriculture_machinery|shipping_|aviation|industry:|St_primary" $C | cut -c1-120 | head -50
echo ---- registry
grep -E "^share_bev|^share_land|bev" research_inputs/registry_v5/DATA_REGISTRY.csv | cut -c1-260 | head -12
echo ---- upstream add_EVs
grep -n "def add_EVs\|def add_land_transport\|bev_dsm\|v2g\|avail_profile\|dsm_profile\|number_cars\|nodal_transport" scripts/prepare_sector_network.py | cut -c1-140 | head -30
echo ---- LP sizes
grep -n "rows\|cols\|nonzero" research/06_scope_redesign/p1_b4p_20261026/B4P_REPORT.md | cut -c1-240 | head -12
