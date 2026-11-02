#!/bin/bash
grep -ln "smoke_v2\|m08b_smoke_eval" /home/jin/dfx3/*.sh | head -5
f=$(grep -ln "smoke_v2" /home/jin/dfx3/*.sh | head -1); echo "== $f"; cut -c1-230 "$f" | head -44
echo "== eval"; sed -n 1,60p /home/jin/wt_v3_20261102/scripts_project/m08b_smoke_eval.py | cut -c1-200
ls /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/smoke_v2/ /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/smoke_v2/* | head -40
env | grep -c GRB_LICENSE; ls -la /home/jin/gurobi.lic | cut -c1-60
