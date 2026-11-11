#!/bin/bash
# X20：测 pypsa 导入耗时，比较 PYTHONPYCACHEPREFIX 指向 D 盘（9p）与不设（用环境自带 __pycache__，不新写）
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
export PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=$PROJ_DATA
cd /home/jin
for i in 1 2; do
  s=$(date +%s.%N); PYTHONPYCACHEPREFIX=$D/pycache $PY -c 'import pypsa, xarray, pandas' ; e=$(date +%s.%N); echo "prefix_on_D run$i $(echo "$e - $s" | bc) s"
  s=$(date +%s.%N); env -u PYTHONPYCACHEPREFIX PYTHONDONTWRITEBYTECODE=1 $PY -c 'import pypsa, xarray, pandas' ; e=$(date +%s.%N); echo "no_prefix run$i $(echo "$e - $s" | bc) s"
done
