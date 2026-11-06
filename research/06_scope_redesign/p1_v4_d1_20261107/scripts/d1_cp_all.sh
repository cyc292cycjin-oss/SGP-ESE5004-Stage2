#!/bin/bash
# D1 sections 5.4 / 7.1: repository checkpoints of the three W08 sets against the reference engine results (W08 ref_main / ref_iid / ref_i2chk).
# The T03 verdict keeps every value, so the post-section-5 reference equals the W08 reference (potential file byte-identical, SHA256 cd9df282...).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d1_20261107; R=/home/jin/wt_v4_d1; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d1
export PYTHONHASHSEED=0
cd $R || exit 1
run() {   # label ref steps args...
  label=$1; ref=$2; steps=$3; shift 3
  $PY scripts_project/v4_industry.py --checkpoints $T/cp_$label --steps $steps --work $T/work_cp_$label "$@" > $T/cp_$label.log 2>&1 || { echo "CHAIN_FAILED $label"; tail -20 $T/cp_$label.log; return 1; }
  $PY $W/scripts/d1_checkpoints.py $T/cp_$label /home/jin/v4w08/ref_$ref/results $label --steps $steps; echo "CP_$label:exit=$?"
}
run main main S0,S1,S2,S3,S4,S5a,S5b,S5c,S5d,S5e,S5f,S5g,S6a,S6b,S6c,S7 --anchor-mode ras
run iid iid S1,S2,S3,S4,S5a,S5b,S5c,S5d,S5e,S5f,S5g,S6a,S6b,S6c,S7 --anchor-mode iid
run i2chk i2chk S1,S7 --anchor-mode iid --set id_paper_fuelwood=purchased
echo "ALL_DONE"
