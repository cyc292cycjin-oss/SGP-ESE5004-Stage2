#!/bin/bash
# M08b supplement 01: copy the supplement-01 build / variant status files and build receipts into the work evidence folder; tabulate the variant receipts
set -u
M=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b
E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08b_20261021/evidence
cp $M/builds_s01/BUILD_STATUS.txt $E/M08B_S01_BUILD_STATUS.txt
cp $M/variants_s01/VARIANT_STATUS.txt $E/M08B_S01_VARIANT_STATUS.txt
for s in integrated disconnected; do cp $M/builds_s01/$s/${s}_BUILD_RECEIPT.json $E/M08B_S01_${s}_BUILD_RECEIPT.json; done
/home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/m08b_variant_receipts.py --variants $M/variants_s01 --tag S01
ls -la $E | grep S01
