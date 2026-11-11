#!/bin/bash
# X20 ①1 试跑：v5_wind_gwa.py（尚未放进 worktree）输出到 D 盘 cache/wind_gwa；内存门槛：可用 >= 4 GiB 且预计峰值 1.5 GiB <= 可用 / 2
set -u
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
export PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj PYTHONHASHSEED=0
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); PEAK=1610612736
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK"; exit 3; fi
echo "MEM_OK available=$AV peak_est=$PEAK"
cd $D/x20_src/scripts_project || exit 2
/usr/bin/time -v $PY - <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, ".")
import v5_wind_gwa as m
m.GIPT = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x03_renew_20261111/cache/code/research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv")
m.main(["--gwa-dir", "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x03_renew_20261111/downloads/gwa",
        "--output", "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/cache/wind_gwa",
        "--cutout", "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/cutouts/asean_zenodo_20325289/cutout-2013-era5.nc"])
EOF
echo "exit=$?"
