#!/bin/bash
# Generic constraint / dual handling that could see the bunker row without naming it (instruction 2.3). Read-only.
set -u
cd /home/jin/wt_v3_fix
echo "== research_country_co2_limit / research_co2_storage_cap / research_ prefix enumerations"
git grep -n -E 'research_country_co2_limit|research_co2_storage_cap|startswith\(.research_|"research_" ?in|research_\*' -- scripts_project tests '*.sh' | cut -c1-240
echo
echo "== .dual / dual dataset / clabels consumers in scripts_project"
git grep -n -l -E '\.dual\b|dual_dataset|clabels|constraints\[|m\.constraints|\.constraints\.items|for .* in .*constraints' -- scripts_project | sort
echo
echo "== net_zero_rows / tagged rows"
git grep -n -E 'net_zero_rows|row_ref\[' -- scripts_project | cut -c1-240
