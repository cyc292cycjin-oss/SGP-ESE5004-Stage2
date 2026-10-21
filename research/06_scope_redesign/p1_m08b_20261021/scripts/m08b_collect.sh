#!/bin/bash
# M08b: copy build / variant status files and build receipts into the work evidence folder
set -u
M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b
E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08b_20261021/evidence
cp $M/builds/BUILD_STATUS.txt $E/M08B_BUILD_STATUS.txt
cp $M/variants/VARIANT_STATUS.txt $E/M08B_VARIANT_STATUS.txt
for s in integrated disconnected; do cp $M/builds/$s/${s}_BUILD_RECEIPT.json $E/M08B_${s}_BUILD_RECEIPT.json; done
ls -la $E
