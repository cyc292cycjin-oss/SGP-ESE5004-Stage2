#!/bin/bash
# trace LA plant ids to names (read-only)
W=/home/jin/wt_v3_20261102; M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
cd $M
timeout 60 grep -rlE 'G100000602432|3c3734e2f61b|3b26fcde74e2' research_inputs results_project/s4a results_project/s1 resources 2>/dev/null | head -12
echo ---
ls research_inputs | tr '\n' ' ' | cut -c1-600; echo
ls research_inputs/fleet* research_inputs/existing* 2>/dev/null | head -30
grep -n "EXISTING_FLEET_S4A\|FLEET\b\|\.csv" $W/scripts_project/s4a_2_fleet_data.py | head -30
