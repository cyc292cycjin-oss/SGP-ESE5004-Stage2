#!/bin/bash
# D2a sections 2 / 5: repository checkpoints of the three switch sets against the corrected reference engine results (scripts/ref_runs.sh ->
# /home/jin/v4d2a/ref_<n>/results). The F-01 sensitivity set (residue_literal) has no reference engine option: it is compared with the Fable EXACT numbers in
# tests/research/test_v4_d2a_fixes.py instead.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107; R=/home/jin/wt_v4_d2a; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d2a
export PYTHONHASHSEED=0
cd $R || exit 1
run() {   # label ref steps args...
  label=$1; ref=$2; steps=$3; shift 3
  $PY scripts_project/v4_industry.py --checkpoints $T/cp_$label --steps $steps --work $T/work_cp_$label "$@" > $T/cp_$label.log 2>&1 || { echo "CHAIN_FAILED $label"; tail -20 $T/cp_$label.log; return 1; }
  $PY $W/scripts/d2a_checkpoints.py $T/cp_$label $T/ref_$ref/results $label --steps $steps; echo "CP_$label:exit=$?"
}
run main main S0,S1,S2,S3,S4,S5a,S5b,S5c,S5d,S5e,S5f,S5g,S6a,S6b,S6c,S7 --anchor-mode ras
run iid iid S1,S2,S3,S4,S5a,S5b,S5c,S5d,S5e,S5f,S5g,S6a,S6b,S6c,S7 --anchor-mode iid
run i2chk i2chk S1,S7 --anchor-mode iid --set id_paper_fuelwood=purchased
echo ALL_DONE
