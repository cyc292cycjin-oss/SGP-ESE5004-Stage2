#!/bin/bash
export PYTHONHASHSEED=0
P=/home/jin/miniforge3/envs/pypsa-earth/bin/python; R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
E=/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence/smoke
cd /home/jin/wt_v3_20261102
env -u GRB_LICENSE_FILE $P scripts_project/v3_smoke_eval.py --run $R/v3/smoke_r2 --out $E --v2-run $R/dfx_v3/smoke_v2 2>&1 | grep -v PROJ | head -9 | cut -c1-100
$P /home/jin/v3/sm_owen.py 2>&1 | cut -c1-760
du -sh $R/v3 | cut -f1
ls -la $E | cut -c25-
