#!/bin/bash
W=/home/jin/wt_v3_20261102; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_s4r_downloads_20261020/F1_renewable_potential
cd $W
echo "== registry fragments"; grep -n "FRAGMENTS\|def main\|sys.exit\|raise" scripts_project/d1_registry.py | cut -c1-140 | head -14; sed -n "$(grep -n 'FRAGMENTS *=' scripts_project/d1_registry.py | head -1 | cut -d: -f1),+6p" scripts_project/d1_registry.py | cut -c1-200
echo "== fleet km sources"; ls research_inputs/registry_v5/sources/jrc_idees_2021/EU27 2>/dev/null | head; ls /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/research_inputs/registry_v5/sources/jrc_idees_2021/EU27 2>/dev/null | head
grep -rIl "number cars\|Number of cars\|vehicle-km\|vkm" research_inputs/registry_v5/*.csv scripts/*.py 2>/dev/null | head
find /home/jin/research/SGP_ESE5004_Stage2/pypsa-asean -maxdepth 3 \( -iname '*vehicle*' -o -iname '*cars*' -o -iname 'transport_data*' \) 2>/dev/null | head
echo "== APG zip"; unzip -l "$S/ESI_APG_Model_v2.3.zip" 2>/dev/null | tail -14 | cut -c1-110
echo "== repo corridors"; ls research_inputs/corridors/ | head -20; grep -rIl "APG\b" research_inputs/corridors/*.csv | head; 
sed -n 1,3p research_inputs/corridors/cross_border_corridors.csv | cut -c1-260
