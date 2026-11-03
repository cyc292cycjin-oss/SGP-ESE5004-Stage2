#!/bin/bash
export PYTHONHASHSEED=0
W=/home/jin/wt_v3_hpc; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $W/scripts_project
$PY v3_data.py 2>&1 | tail -3
$PY d1_registry.py 2>&1 | tail -3
cd $W
git status --short | cut -c1-100
git diff --stat
sha256sum research_inputs/registry_v5/DATA_REGISTRY.csv research_inputs/registry_v5/fragments/v3.csv
$PY - <<'P'
import pandas as pd, subprocess, io
for f in ("research_inputs/registry_v5/fragments/v3.csv", "research_inputs/registry_v5/DATA_REGISTRY.csv"):
    old = pd.read_csv(io.StringIO(subprocess.run(["git", "show", "HEAD:" + f], capture_output=True, text=True).stdout), dtype=str, keep_default_na=False).set_index("param_id")
    new = pd.read_csv(f, dtype=str, keep_default_na=False).set_index("param_id")
    print(f, len(old), len(new), "index equal", list(old.index) == list(new.index))
    for c in new.columns:
        d = old.index[(old[c] != new.loc[old.index, c])]
        if len(d): print("  ", c, list(d))
P
