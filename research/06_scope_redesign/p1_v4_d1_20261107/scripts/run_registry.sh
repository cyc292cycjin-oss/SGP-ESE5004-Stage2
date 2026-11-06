#!/bin/bash
# D1: registry fragment v4_d1 (+ corrections), assembly; diff of DATA_REGISTRY.csv against HEAD (added / changed rows listed).
set -u
R=/home/jin/wt_v4_d1; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d1
export PYTHONHASHSEED=0
cd $R || exit 1
git show HEAD:research_inputs/registry_v5/DATA_REGISTRY.csv > $T/DATA_REGISTRY_head.csv
$PY scripts_project/v4_d1_registry.py || exit 1
$PY scripts_project/d1_registry.py > $T/d1_registry.log 2>&1 || { tail -20 $T/d1_registry.log; exit 1; }
tail -2 $T/d1_registry.log | cut -c1-300
$PY - <<'P'
import pandas as pd
a = pd.read_csv("/home/jin/v4d1/DATA_REGISTRY_head.csv", dtype=str, keep_default_na=False).set_index("param_id")
b = pd.read_csv("/home/jin/wt_v4_d1/research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
gone = sorted(set(a.index) - set(b.index)); new = sorted(set(b.index) - set(a.index))
common = sorted(set(a.index) & set(b.index))
changed = [p for p in common if not a.loc[p].equals(b.loc[p])]
print("rows before", len(a), "after", len(b), "removed", len(gone), "added", len(new), new, "changed", len(changed))
for p in changed:
    cols = [c for c in a.columns if a.at[p, c] != b.at[p, c]]
    print("  CHANGED", p, {c: (a.at[p, c][:60], b.at[p, c][:60]) for c in cols})
P
git status --short research_inputs/registry_v5 | head -20
