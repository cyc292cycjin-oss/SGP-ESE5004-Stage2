#!/bin/bash
# Scaling / hook checks / split stages that could touch the bunker row. Read-only.
set -u
cd /home/jin/wt_v3_fix
echo "== s3b_scaling.py: functions and name-based selections"
grep -n -E '^def |SINGLE_STORE|startswith|constraints\[|Link-p|Store-e|co2|bunker|atmosphere' scripts_project/s3b_scaling.py | cut -c1-220
echo
echo "== s2_solve.py: hooks, scaling calls, split stages, B1_BUNKERS"
grep -n -E 'hooks|scale_|s3b_scaling|split_stage|split-stage|B1_BUNKERS|bunker|export_lp|clabels|DUALS|s4m_duals' scripts_project/s2_solve.py | cut -c1-220 | head -80
echo
echo "== b4_split_solve.py: constraint names?"
grep -n -E 'constraint|bunker|research_' scripts_project/b4_split_solve.py | cut -c1-200 | head -20
echo
echo "== assembly_components.install_research_constraint_hooks"
sed -n '90,175p' scripts_project/assembly_components.py
