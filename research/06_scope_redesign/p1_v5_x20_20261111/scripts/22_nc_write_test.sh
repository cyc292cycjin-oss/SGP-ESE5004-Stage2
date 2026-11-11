#!/bin/bash
# 只写一个 1 KB 级的小 netCDF 到 D 盘，检查 9p 上 HDF5 文件锁是否可用（决定构建输出能否直接写 D 盘）
set -u
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/tmp
mkdir -p $D
for lock in default FALSE; do
  if [ $lock = FALSE ]; then export HDF5_USE_FILE_LOCKING=FALSE; fi
  $PY - <<'EOF'
import os, numpy as np, xarray as xr, pypsa
p = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/tmp/nc_test_%s.nc" % os.environ.get("HDF5_USE_FILE_LOCKING", "default")
try:
    n = pypsa.Network(); n.add("Bus", "b"); n.export_to_netcdf(p); m = pypsa.Network(p)
    print("lock", os.environ.get("HDF5_USE_FILE_LOCKING", "default"), "OK", os.path.getsize(p), list(m.buses.index))
except Exception as e:
    print("lock", os.environ.get("HDF5_USE_FILE_LOCKING", "default"), "FAIL", type(e).__name__, str(e)[:200])
EOF
done
rm -f $D/nc_test_*.nc
