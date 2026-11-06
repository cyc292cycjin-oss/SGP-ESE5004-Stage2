#!/bin/bash
# D1 section 2 item 2: chain check of the HVC basis switch against the I2 sensitivity hvc_s2 (I2 main = anchor iid + ID paper fuelwood purchased):
# S7 checkpoints of the repository chain with hvc_basis b and a; compared with I2_SENSITIVITY_RUNS.csv (T_v2 of hvc_s2 and T_v2 - dT_v2 = I2 main).
set -u
R=/home/jin/wt_v4_d1; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d1; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d1_20261107
export PYTHONHASHSEED=0
cd $R || exit 1
for b in b a; do
  $PY scripts_project/v4_industry.py --checkpoints $T/cp_i2hvc_$b --steps S7 --work $T/work_i2hvc --anchor-mode iid --set id_paper_fuelwood=purchased --set hvc_basis=$b > $T/cp_i2hvc_$b.log 2>&1 || { tail -20 $T/cp_i2hvc_$b.log; exit 1; }
done
$PY $W/scripts/d1_hvc_chain_cmp.py $T/cp_i2hvc_b/step_S7.json $T/cp_i2hvc_a/step_S7.json /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/I2/tables/I2_SENSITIVITY_RUNS.csv $W/tables/D1_HVC_CHAIN_CHECK.csv
