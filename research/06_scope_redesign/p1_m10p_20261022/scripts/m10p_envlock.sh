#!/bin/bash
# M10P-4 (instruction section 4.3; S4N supplement 01 B1 practice): lock files of the local reference environment (WSL conda env pypsa-earth, used by
# the M08b / M12b builds and smokes and by the M10P dry run) for the non-clone cloud install -> research/06_scope_redesign/p1_m10p_20261022/cloud_package/env/
#   ENV_LOCK.txt               python version, key packages, pip list --format=freeze, conda list --export (home path shown as ~)
#   conda_explicit_linux64.txt conda list --explicit --md5 (exact builds with checksums; install without solving)
#   pip_only.txt               packages installed from PyPI (channel pypi), exact versions
#   ENV_DOWNLOAD.json          download size of the conda packages from conda-meta (size field), per channel, largest packages
set -u
ENV=/home/jin/miniforge3/envs/pypsa-earth; PY=$ENV/bin/python; CONDA=/home/jin/miniforge3/bin/conda
O=/home/jin/wt_m10p_20261022/research/06_scope_redesign/p1_m10p_20261022/cloud_package/env; mkdir -p $O
T=$(mktemp -d)
$PY -m pip list --format=freeze 2>/dev/null > $T/pip.txt
$CONDA list -p $ENV --export 2>/dev/null | sed "s#/home/jin#~#g" > $T/conda.txt
$CONDA list -p $ENV --explicit --md5 2>/dev/null | sed "s#/home/jin#~#g" > $O/conda_explicit_linux64.txt
$CONDA list -p $ENV 2>/dev/null | awk '$NF=="pypi" {print $1"=="$2}' > $O/pip_only.txt
{
  echo "# M10P-4 local reference environment (WSL Ubuntu, conda env pypsa-earth at ~/miniforge3/envs/pypsa-earth)"
  echo "# written $(TZ=Asia/Singapore date '+%F %T') SGT; the environment of the M08b / M12b builds and smokes and of the M10P dry run"
  echo "# $($PY --version 2>&1)"
  echo "# platform: $($PY -c 'import platform; print(platform.platform())' 2>/dev/null)"
  echo "# conda $($CONDA --version 2>&1 | awk '{print $2}')"
  echo "# key packages (S4N supplement 01 B3 list; must be identical on the instance):"
  $PY - <<'P' 2>/dev/null
import importlib.metadata as md
for m in ("pypsa", "linopy", "xarray", "pandas", "numpy", "scipy", "gurobipy", "netCDF4", "h5netcdf", "dask", "pyomo", "highspy"):
    try:
        v = md.version(m)
    except md.PackageNotFoundError:
        v = "NOT INSTALLED"
    print("#   %-10s %s" % (m, v))
P
  echo "#"
  echo "# ---- pip list --format=freeze ($(wc -l < $T/pip.txt) packages)"
  cat $T/pip.txt
  echo "#"
  echo "# ---- conda list --export ($(grep -vc '^#' $T/conda.txt) lines)"
  sed 's/^/# /' $T/conda.txt
} > $O/ENV_LOCK.txt
$PY - $ENV $O/ENV_DOWNLOAD.json <<'P'
import collections, glob, json, sys
rows = [json.load(open(f)) for f in glob.glob(sys.argv[1] + "/conda-meta/*.json")]
ch = collections.Counter()
for r in rows:
    ch[r.get("channel", "").rstrip("/").split("/")[-1]] += int(r.get("size") or 0)
tot = sum(int(r.get("size") or 0) for r in rows)
big = sorted(((int(r.get("size") or 0), r["name"], r["version"]) for r in rows), reverse=True)[:10]
json.dump(dict(conda_packages=len(rows), download_bytes=tot, download_gib=tot / 2**30, bytes_by_channel=dict(ch), missing_size=sum(1 for r in rows if not r.get("size")),
               largest=[dict(name=n, version=v, bytes=s) for s, n, v in big], installed_note="installed environment on disk ~3.3 GiB (du, local)",
               source="conda-meta/*.json size field (tarball bytes) of the local environment"), open(sys.argv[2], "w"), indent=1)
print("conda packages", len(rows), "download bytes", tot)
P
rm -rf $T
echo "explicit lines: $(grep -c '^https' $O/conda_explicit_linux64.txt); pip only: $(cat $O/pip_only.txt | tr '\n' ' ')"
echo "SENSITIVE_SCAN:"; grep -iE "secret|password|licen[cs]e[i]d|wlsaccess|api[_-]?key" $O/* | head -5
head -22 $O/ENV_LOCK.txt
