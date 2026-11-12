#!/bin/bash
# X21 开关（决策 253）的系数表：v5_onwind_reference_data.py，网络 = C-2 预构建 F1（提交 9622c78d），GWA 毛值 = X03 cache/onwind_cells/onwind_node_cells.csv
set -u
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; LOG=$D/logs/89_reference_factors.log
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
AV=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo); [ "$AV" -ge 4608 ] || { echo "GATE REFUSED $AV"; exit 3; }
cd $R || exit 1
{ echo "MemAvailable_MiB $AV"
$PY scripts_project/v5_onwind_reference_data.py --network $D/builds/c2pre/integrated/integrated_2920_3h_unsolved.nc --cells /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x03_renew_20261111/cache/onwind_cells/onwind_node_cells.csv 2>&1 | grep -v -e Warning -e PROJ -e pypsa.io
sha256sum research_inputs/renewable_v5/ONWIND_REFERENCE_LEVEL_FACTORS_V5.csv; } > $LOG 2>&1
cat $LOG
