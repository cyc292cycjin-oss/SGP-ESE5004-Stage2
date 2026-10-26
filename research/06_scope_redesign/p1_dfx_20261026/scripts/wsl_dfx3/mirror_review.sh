#!/bin/bash
# DFX v3: mirror the demand-review scripts, tables and evidence from the Windows work folder into the deliverable folder of the worktree (no git).
set -eu
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026
D=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026
mkdir -p $D/scripts/review $D/review $D/evidence
cp $W/scripts/dfx_demand_review.py $W/scripts/dfx_first_order.py $D/scripts/review/
cp $W/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v1.csv $W/DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv $W/DEMAND_DIFF_V2_V1.csv $W/DFX_BRIDGE_V2.csv $W/DFX_ELECTRICITY_PER_CAPITA_V2.csv $W/DFX_FIRST_ORDER.md $D/review/
cp $W/evidence/DFX_D1_CHECKS_v1.json $W/evidence/DFX_D1_CHECKS_v2.json $W/evidence/DFX_DEMAND_DIFF_SUMMARY.json $W/evidence/DFX_BRIDGE_V2.json $W/evidence/DFX_FIRST_ORDER.json $D/evidence/
du -sh $D/review $D/evidence $D/scripts/review
ls -la $D/review $D/evidence $D/scripts/review
