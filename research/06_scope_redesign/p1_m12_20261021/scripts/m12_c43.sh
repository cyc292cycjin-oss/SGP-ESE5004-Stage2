#!/bin/bash
# M12 C4.3: pipeline run on the pre-correction 365x24h results (S4N pilot integrated + S4O-6 disconnected); outputs in NEW folders only.
set -u
export PYTHONHASHSEED=0
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
REPO=/home/jin/wt_m12_20261021
W=/mnt/d/ResearchWorkspaces/ASEAN/work
S4N=$W/p1_step4n_20261019/cloud_results/20261019T072454Z_5125/full/export/integrated
S4O=$W/p1_step4o_20261019/cloud_results/20261019T162951Z_6896
OUT=${OUT:-$W/p1_m12_20261021/evidence/c43}
mkdir -p "$OUT"
cd "$REPO"
STEP=${STEP:-all}
if [ "$STEP" = all ] || [ "$STEP" = int ]; then
  /usr/bin/time -v $PY scripts_project/m12_allocation.py run --repo "$REPO" --solve-dir "$S4N" --scenario integrated --label S4N_PILOT_FORMAL_TRIAL_365X24H \
    --precision "$S4O/top/pilot_integrated/PRECISION.json" --out "$OUT/s4n_integrated" > "$OUT/s4n_integrated.log" 2> "$OUT/s4n_integrated.err"
  echo "INT:exit=$?"
fi
if [ "$STEP" = all ] || [ "$STEP" = dis ]; then
  /usr/bin/time -v $PY scripts_project/m12_allocation.py run --repo "$REPO" --solve-dir "$S4O/full/unpacked/disconnected" --scenario disconnected --label S4O6_FORMAL_TRIAL_365X24H \
    --out "$OUT/s4o_disconnected" > "$OUT/s4o_disconnected.log" 2> "$OUT/s4o_disconnected.err"
  echo "DIS:exit=$?"
fi
if [ "$STEP" = all ] || [ "$STEP" = ben ]; then
  $PY scripts_project/m12_allocation.py benefit --repo "$REPO" --integrated "$OUT/s4n_integrated" --disconnected "$OUT/s4o_disconnected" --out "$OUT/benefit" \
    --integrated-dual "$OUT/../c2/full_365x24h/RHS_AUDIT.json" --disconnected-dual "$OUT/../c2/disconnected_365x24h/RHS_AUDIT.json" > "$OUT/benefit.log" 2> "$OUT/benefit.err"
  echo "BEN:exit=$?"
fi
tail -3 "$OUT"/*.log
grep -E "Maximum resident|Elapsed" "$OUT"/*.err
