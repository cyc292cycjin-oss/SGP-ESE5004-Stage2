#!/bin/bash
# D2b section 7: refresh of the D2a rerank and the W19 candidates (no solver). The D2a rerank script (copy rerank_with_results_d2b.py, method unchanged) on the
# v3.1 2920x3h results - reference v31 (F1, F2), control v31ev05 (F3, F4) - with this branch's registry ranges (--registry-ranges) and the D2b inventory
# overrides (scripts/d2b_inventory.py); the extract cache is the D2a delivery's cache/ folder, used read-only (instruction section 7: reuse the D2a cache).
# Then the D2b post-processing (TOP30, Owen top 10, difference to the D2a rerank, W19_CANDIDATES_D2B.csv).
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2b_20261108; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D2A=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107; EXP=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_results_v31/unpacked/export
export PYTHONHASHSEED=0
mkdir -p $W/rerank
[ "$(ps -eo args= | grep -cE '[s]2_solve\.py|[g]urobi_cl')" = 0 ] || { echo "REFUSED: a solve is running"; exit 2; }
cd $W || exit 1
for d in 7508ec72ddce9a9d_v1 4cc51892d748805f_v1 8c25962bc40abfd9_v1 8d1ae106154c33ee_v1; do [ -e $D2A/cache/$d/DONE ] || { echo "REFUSED: D2a cache $d incomplete"; exit 3; }; done
$PY scripts/d2b_inventory.py /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w10_20261106/C_GRADE_INVENTORY.csv $W/rerank/C_GRADE_INVENTORY_D2B_INPUT.csv || exit 1
$PY scripts/rerank_with_results_d2b.py --set v31=$EXP/F1,$EXP/F2 --set v31ev05=$EXP/F3,$EXP/F4 --reference v31 \
    --inventory $W/rerank/C_GRADE_INVENTORY_D2B_INPUT.csv --repo /home/jin/wt_v4_d2b --cache $D2A/cache --out $W/rerank --registry-ranges \
    > $W/logs/rerank_run.txt 2>&1; echo "RERANK_EXIT:$?"; tail -20 $W/logs/rerank_run.txt
$PY scripts/rerank_d2b_post.py --rerank $W/rerank --d2a $D2A/rerank --inventory $W/rerank/C_GRADE_INVENTORY_D2B.csv --out $W > $W/logs/rerank_post.txt 2>&1; echo "POST_EXIT:$?"; tail -60 $W/logs/rerank_post.txt
echo RERANK_DONE
