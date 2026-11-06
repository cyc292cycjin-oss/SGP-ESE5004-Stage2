#!/bin/bash
# W08: why test_s1_built_networks fails - S1 network metadata vs cross-border switches of the config at the W08 head and at the start aad8e476
export PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj; R=/home/jin/wt_v4_w08; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $R || exit 1
ls -la results_project/s1 | head -3
git diff --stat aad8e476 HEAD -- configs/
$PY - <<'PY'
import json, subprocess, sys, yaml, logging
logging.disable(logging.CRITICAL)
sys.path.insert(0, "scripts_project")
import pypsa
n = pypsa.Network("results_project/s1/integrated/integrated_2920_3h_unsolved.nc")
print("meta switches", n.meta.get("research_cross_border", {}).get("switches"))
from phase4_static import config
from pathlib import Path; c = config(Path("."))
def find(d, path=""):
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "cross_border": print("config", path + str(k), {kk: vv for kk, vv in v.items() if not isinstance(vv, dict)} if isinstance(v, dict) else v)
            find(v, path + str(k) + ".")
find(c)
for ref in ("aad8e476", "HEAD"):
    out = subprocess.run(["git", "show", f"{ref}:configs/research/baseline.yaml"], capture_output=True, text=True).stdout
    y = yaml.safe_load(out)
    print(ref, "research.cross_border", json.dumps(y.get("research", {}).get("cross_border"), sort_keys=True)[:400])
PY
