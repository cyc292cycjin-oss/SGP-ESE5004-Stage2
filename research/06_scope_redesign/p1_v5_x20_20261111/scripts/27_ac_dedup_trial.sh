#!/bin/bash
# X20 ②2 试跑：v5_ac_dedup_data.py（尚未放进 worktree），ROOT 指向 D 盘代码副本（data/osm-plus-prebuilt、regions_onshore 相同）；输出到 D 盘 cache/ac_dedup
set -u
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
export PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj PYTHONHASHSEED=0
AV=$(awk '/MemAvailable/ {print $2*1024}' /proc/meminfo); PEAK=1073741824
if [ "$AV" -lt 4294967296 ] || [ "$PEAK" -gt $((AV / 2)) ]; then echo "MEM_REFUSED available=$AV peak_est=$PEAK"; exit 3; fi
echo "MEM_OK available=$AV peak_est=$PEAK"
mkdir -p $D/cache/ac_dedup
cd $D/x20_src/scripts_project || exit 2
/usr/bin/time -v $PY - <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, ".")
import v5_ac_dedup_data as m
C = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x03_renew_20261111/cache/code")
m.OSM = C / "data/osm-plus-prebuilt/0.1.1"
m.main(["--network", "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w14/builds/main/integrated/integrated_2920_3h_unsolved.nc",
        "--tags", "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/cache/osm/WAY_TAGS_V5.csv",
        "--output", "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/cache/ac_dedup/AC_DEDUP_V5.csv"])
EOF
echo "exit=$?"
