#!/bin/bash
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
ls $R/results_project/ | head -60
echo ---; ls -la $R/results_project/dfx_v3/ 2>/dev/null | head -30
echo ---; find $R/results_project/dfx_v3 -maxdepth 3 -name '*unsolved.nc' -printf '%s %p\n' 2>/dev/null | head -20
echo --- builder scripts; ls /home/jin/dfx3 | head -40
grep -ln "s2_network.py" /home/jin/dfx3/* 2>/dev/null | head
echo --- python; grep -hE "PY=|python" /home/jin/dfx3/*.sh 2>/dev/null | head -8
ls -d /home/jin/*/envs/* 2>/dev/null | head; ls /home/jin | head -80
grep -rn "gate_b6_cost\|existing_cross_border_fom" $R/../research_model/scripts_project/s2_solve.py | head -3
cd /home/jin/wt_v3_20261102/scripts_project; grep -ln "existing_cross_border_fom_eur" *.py v5/*.py | head -30
