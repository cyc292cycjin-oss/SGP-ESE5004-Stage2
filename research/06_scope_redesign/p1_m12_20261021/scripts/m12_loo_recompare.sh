#!/bin/bash
# M12 C2: re-run only the right-hand-side comparison of the leave-one-out variants (no model build)
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
REPO=/home/jin/wt_m12_20261021
EV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12_20261021/evidence/c2
cd "$REPO"
for c in BN ID KH LA MM MY PH SG TH TL VN; do
  echo "LOO24_$c:$($PY scripts_project/m12_rhs_audit.py loo --full "$EV/loo_trunc24/full/RHS_BY_FAMILY_OWNER.csv" --variant "$EV/loo_trunc24/minus_$c/RHS_BY_FAMILY_OWNER.csv" --removed "$c" --out "$EV/loo_trunc24/minus_$c")"
done
echo "LOO365_VN:$($PY scripts_project/m12_rhs_audit.py loo --full "$EV/full_365x24h/RHS_BY_FAMILY_OWNER.csv" --variant "$EV/minus_VN_365x24h/RHS_BY_FAMILY_OWNER.csv" --removed VN --out "$EV/minus_VN_365x24h")"
