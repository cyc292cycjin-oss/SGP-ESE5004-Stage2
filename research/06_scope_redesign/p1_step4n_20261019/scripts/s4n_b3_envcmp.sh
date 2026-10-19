#!/bin/bash
# S4N supplement 01 B3.1: instance environment vs local (pip list --format=freeze of the pypsa-earth env on both sides); key packages must match exactly.
# Host and port from the calling command line environment only. Writes the comparison to the work folder (no host / port in it).
set -u
source /home/jin/s4n_ssh.sh
O=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/evidence/s4n_2; mkdir -p $O
RPY=/root/miniconda3/envs/pypsa-earth/bin/python
s4n_ssh "$RPY --version 2>&1; $RPY -m pip list --format=freeze 2>/dev/null" > $O/ENV_INSTANCE_PIP_LIST.txt || { echo "REMOTE ENV MISSING"; exit 1; }
/home/jin/miniforge3/envs/pypsa-earth/bin/python -m pip list --format=freeze 2>/dev/null > $O/ENV_LOCAL_PIP_LIST.txt
/home/jin/miniforge3/envs/pypsa-earth/bin/python - $O <<'P'
import json, sys
from pathlib import Path
o = Path(sys.argv[1])
def load(p):
    lines = p.read_text().splitlines(); py = lines[0].split()[-1] if lines and lines[0].startswith("Python") else None
    d = {}
    for l in lines:
        if "==" in l:
            k, v = l.split("==", 1); d[k.lower().replace("_", "-")] = v
    return py, d
rpy, R = load(o / "ENV_INSTANCE_PIP_LIST.txt"); _, L = load(o / "ENV_LOCAL_PIP_LIST.txt")
import platform; lpy = platform.python_version()
KEY = ["pypsa", "linopy", "xarray", "pandas", "numpy", "scipy", "gurobipy", "netcdf4", "h5netcdf", "dask", "pyomo", "highspy"]
key = {k: dict(local=L.get(k), instance=R.get(k), equal=(L.get(k) == R.get(k))) for k in KEY}
key["python"] = dict(local=lpy, instance=rpy, equal=(lpy == rpy))
only_l = sorted(set(L) - set(R)); only_r = sorted(set(R) - set(L)); diff = {k: [L[k], R[k]] for k in sorted(set(L) & set(R)) if L[k] != R[k]}
res = dict(key_packages=key, key_all_equal=all(v["equal"] for v in key.values()), local_packages=len(L), instance_packages=len(R),
           only_local=only_l, only_instance=only_r, version_differences=diff)
(o / "ENV_COMPARE.json").write_text(json.dumps(res, indent=1))
print(json.dumps(dict(key_all_equal=res["key_all_equal"], key={k: (v["local"], v["instance"]) for k, v in key.items()}, counts=[len(L), len(R)],
                      only_local=only_l[:20], only_instance=only_r[:20], n_version_differences=len(diff), version_differences=dict(list(diff.items())[:30])), indent=1))
P
