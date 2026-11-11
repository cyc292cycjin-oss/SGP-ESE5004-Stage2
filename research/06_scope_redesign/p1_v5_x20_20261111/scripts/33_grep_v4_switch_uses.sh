#!/bin/bash
cd /home/jin/wt_v5_x20
grep -n -E 'C\.switches\(|v4_common\.switches|\bswitches\(|out_name\(|is_main_set\(|BIOMASS_POTENTIAL_FILES|V4_SWITCHES|check_network_meta\(' scripts_project/*.py scripts_project/v5/*.py 2>/dev/null | grep -v '^scripts_project/v4_common.py' | cut -c1-230
echo ==== v4_industry --set
grep -n -E '"--set"|--set|overrides' scripts_project/v4_industry.py | head -20
