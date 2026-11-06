#!/bin/bash
# W08 checklist section 2: reference inputs dump, cache build in the worktree, quick comparison.
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106; R=/home/jin/wt_v4_w08; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
( cd $W && W08_REF_SCRATCH=/home/jin/v4w08/ref_main $PY scripts/w08_ref_dump.py ) || exit 1
cd $R && $PY scripts_project/v4_industry_cache.py || exit 1
$PY - <<'EOF'
import json, sys
sys.path.insert(0, "/home/jin/wt_v4_w08/scripts_project")
import pandas as pd
import v4_industry_cache as C
from v4_common import V4_MAIN, V31
ref = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w08_20261106/tables/W08_REF_INPUTS.json"))
cells = C.load_cells()
rc = pd.DataFrame(ref["cells"])
print("cells rows", len(cells), len(rc), "mwh equal", bool((cells.mwh.values == rc.mwh.values).all()), "keys equal", bool((cells[["country","tx","code"]].values == rc[["country","tx","code"]].values).all()))
s = dict(V4_MAIN, anchor_mode="ras")
print("cache main == ref cache_a_paper:", C.cache_for(cells, s)["records"] == ref["cache_a_paper"]["records"])
s2 = dict(s, id_paper_fuelwood="purchased")
print("cache purchased == ref cache_a:", C.cache_for(cells, s2)["records"] == ref["cache_a"]["records"])
s3 = dict(s, residue_boundary=False)
print("cache full == ref cache_full:", C.cache_for(cells, s3)["records"] == ref["cache_full"]["records"])
print("fuelwood", C.fuelwood_mean(cells), ref["fw"])
EOF
