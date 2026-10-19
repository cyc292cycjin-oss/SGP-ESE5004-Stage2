#!/bin/bash
# S4N supplement 01 B1.1: full package list of the local WSL environment used by the S4M smokes and S4N-1 (pypsa-earth) -> ENV_LOCK_LOCAL.txt.
# Local editable / local path packages are listed separately; the home path is shown as ~ (no other sensitive content in pip / conda lists).
set -u
ENV=/home/jin/miniforge3/envs/pypsa-earth; PY=$ENV/bin/python
O=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/ENV_LOCK_LOCAL.txt
T=$(mktemp -d)
$PY -m pip freeze 2>/dev/null | sed "s#/home/jin#~#g" > $T/pipraw.txt
$PY -m pip list --format=freeze 2>/dev/null > $T/pip.txt   # name==version for every package (conda-built packages show "@ file:///home/conda/feedstock_root/..." in pip freeze)
# genuinely local / editable: -e lines and file URLs that are not conda build artefacts
grep -E "^-e |@ file:" $T/pipraw.txt | grep -vE "file:///home/conda/feedstock_root|file:///croot|file:///opt/conda/conda-bld|/conda-bld/" > $T/local.txt || true
/home/jin/miniforge3/bin/conda list -p $ENV --export 2>/dev/null | sed "s#/home/jin#~#g" > $T/conda.txt
{
  echo "# S4N supplement 01 B1.1 - local reference environment (WSL Ubuntu, conda env pypsa-earth at ~/miniforge3/envs/pypsa-earth)"
  echo "# written $(TZ=Asia/Singapore date '+%F %T') SGT; used by the S4M-2 smokes, S4M-S2 re-run and S4N-1 (package code f50c8850)"
  echo "# $($PY --version 2>&1)"
  echo "# platform: $($PY -c 'import platform; print(platform.platform())' 2>/dev/null)"
  echo "# key packages (supplement B3 list):"
  $PY - <<'P' 2>/dev/null | grep -v PROJ
import importlib
for m in ("pypsa", "linopy", "xarray", "pandas", "numpy", "scipy", "gurobipy", "netCDF4", "h5netcdf", "dask", "pyomo", "highspy"):
    try:
        mod = importlib.import_module(m)
        v = getattr(mod, "__version__", None) or ".".join(map(str, mod.gurobi.version()))
    except Exception as e:
        v = "NOT INSTALLED"
    print("#   %-10s %s" % (m, v))
P
  echo "#"
  echo "# ---- local editable / local path packages (NOT to be installed on the instance; research code comes from the package): $(wc -l < $T/local.txt)"
  sed "s/^/#   /" $T/local.txt
  echo "# (pip freeze shows $(grep -c 'file:///home/conda/feedstock_root' $T/pipraw.txt) conda-built packages as '@ file:///home/conda/feedstock_root/...'; they are ordinary conda packages, versions below)"
  echo "#"
  echo "# ---- pip list --format=freeze ($(wc -l < $T/pip.txt) packages)"
  cat $T/pip.txt
  echo "#"
  echo "# ---- conda list --export ($(grep -vc '^#' $T/conda.txt) lines)"
  cat $T/conda.txt
} > $O
rm -rf $T
echo "WRITTEN: $(wc -l < $O) lines, $(stat -c %s $O) bytes"
echo "SENSITIVE_SCAN (package names like asttokens excluded):"; grep -iE "secret|password|licen[cs]e[i]d|wlsaccess|api[_-]?key|(^|[^a-z])token[^s]" $O | head -5 | cut -c1-120
head -26 $O
