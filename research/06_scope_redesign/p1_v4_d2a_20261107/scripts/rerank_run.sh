#!/bin/bash
# D2a section 4: the W10 rerank (copy rerank_with_results_d2a.py with the stage-2 method corrections) on the v3.1 2920x3h results - reference v31 (F1, F2),
# control v31ev05 (F3, F4); the W15 extract cache is COPIED into this delivery folder (the W15 folder is not written); the Store e_nom bound duals are read
# from the DUALS_BY_CONSTRAINT.nc files alone (no solved network is opened; the guard in the script refuses a network read with a solver running or < 8 GiB free).
# Then the post-processing (TOP30, Owen top 10, difference to W15, W19 candidates). No solver, no network build.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
W15=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v31_w15_20261106; EXP=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_results_v31/unpacked/export
export PYTHONHASHSEED=0
mkdir -p $W/cache $W/rerank
for d in 7508ec72ddce9a9d_v1 4cc51892d748805f_v1 8c25962bc40abfd9_v1 8d1ae106154c33ee_v1; do
  [ -d $W/cache/$d ] || { cp -r $W15/cache/$d $W/cache/$d; echo "cache $d copied from W15"; }
done
cd $W || exit 1
$PY scripts/rerank_with_results_d2a.py --set v31=$EXP/F1,$EXP/F2 --set v31ev05=$EXP/F3,$EXP/F4 --reference v31 \
    --inventory /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w10_20261106/C_GRADE_INVENTORY.csv --repo /home/jin/wt_v4_d2a --cache $W/cache --out $W/rerank --registry-ranges \
    > $W/logs/rerank.txt 2>&1; echo "RERANK_EXIT:$?"; tail -30 $W/logs/rerank.txt
$PY scripts/rerank_d2a_post.py --rerank $W/rerank --w15 $W15 --inventory $W/rerank/C_GRADE_INVENTORY_D2A.csv --out $W > $W/logs/rerank_post.txt 2>&1; echo "POST_EXIT:$?"; tail -60 $W/logs/rerank_post.txt
echo RERANK_DONE
