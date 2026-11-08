#!/bin/bash
# D2c: registry fragments (W08 fragment: file hashes incl. baseline.yaml; D1; D2a T04 / PHS; D2b T05 / band / data upgrades; D2c T06 trunk dry mass, replanting
# low; corrections), assembly; diff of DATA_REGISTRY.csv against HEAD.
set -u
R=/home/jin/wt_v4_d2c; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d2c
export PYTHONHASHSEED=0
mkdir -p $T
cd $R || exit 1
bash /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2c_20261109/scripts/sync.sh > /dev/null   # the fragments cite files of the D1 / D2a / D2b / D2c deliveries (present in the repository)
for f in v4_d2c v4_d2c_corrections; do [ -e research_inputs/registry_v5/fragments/$f.csv ] || { head -1 research_inputs/registry_v5/fragments/v4_d2b.csv > research_inputs/registry_v5/fragments/$f.csv; echo "placeholder $f.csv (header only; written below by v4_d2c_registry.py)"; }; done
$PY scripts_project/v4_registry.py || exit 1
git show HEAD:research_inputs/registry_v5/DATA_REGISTRY.csv > $T/DATA_REGISTRY_head.csv
$PY scripts_project/v4_d1_registry.py || exit 1
$PY scripts_project/v4_d2a_registry.py || exit 1
$PY scripts_project/v4_d2b_registry.py || exit 1
$PY scripts_project/v4_d2c_registry.py || exit 1
$PY scripts_project/d1_registry.py > $T/d1_registry.log 2>&1 || { tail -20 $T/d1_registry.log; exit 1; }
tail -2 $T/d1_registry.log | cut -c1-300
$PY - <<'P'
import pandas as pd
a = pd.read_csv("/home/jin/v4d2c/DATA_REGISTRY_head.csv", dtype=str, keep_default_na=False).set_index("param_id")
b = pd.read_csv("/home/jin/wt_v4_d2c/research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
gone = sorted(set(a.index) - set(b.index)); new = sorted(set(b.index) - set(a.index))
common = sorted(set(a.index) & set(b.index))
changed = [p for p in common if not a.loc[p].equals(b.loc[p])]
print("rows before", len(a), "after", len(b), "removed", len(gone), gone, "added", len(new), "changed", len(changed))
for p in changed:
    cols = [c for c in a.columns if a.at[p, c] != b.at[p, c]]
    print("  CHANGED", p, {c: (a.at[p, c][:60], b.at[p, c][:60]) for c in cols})
for p in new:
    print("  NEW", p, b.at[p, "value"], b.at[p, "unit"], b.at[p, "tier"], b.at[p, "status"])
P
git status --short research_inputs/registry_v5 | head -20
