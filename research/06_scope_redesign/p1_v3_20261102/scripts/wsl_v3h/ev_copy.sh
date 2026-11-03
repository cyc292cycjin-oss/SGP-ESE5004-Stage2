#!/bin/bash
# copy the step evidence (JSON / CSV / status text only) from results_project/v3hpc into the branch folder evidence/hpc/
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; R=$MAIN/results_project/v3hpc; E=/home/jin/wt_v3_hpc/research/06_scope_redesign/p1_v3_20261102/evidence/hpc
mkdir -p $E/static_sa $E/static_sa_ev05
cp $R/evidence/*.json $E/
cp $R/builds/BUILD_STATUS.txt $E/BUILD_STATUS_F1_F4.txt
for r in sa sa_ev05; do cp $R/builds/$r/static/evidence/* $E/static_$r/; done
ls -la $E | head -20
