#!/bin/bash
# M12b 1.2: re-grade the existing OWEN.json files of M12 supplement 01 with the item-138 dual acceptance (inputs unchanged; no solve)
set -u
WT=/home/jin/wt_m12_20261021; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
EV=$WT/research/06_scope_redesign/p1_m12_20261021/evidence/s01
OUT=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m12b_20261021/evidence/regrade_138
mkdir -p $OUT; cd $WT || exit 1
for t in smoke_56x3h s4o6_disconnected_365x24h s4n_pilot_365x24h; do
  echo "== $t"; PYTHONHASHSEED=0 $PY scripts_project/m12_rhs_audit.py regrade --owen $EV/$t/OWEN.json --out $OUT/${t}_REGRADE_138.json
done
