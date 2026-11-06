#!/bin/bash
# W08 checklist section 10: v4 tables regenerated (final code), registry fragment, registry assembly; diff of DATA_REGISTRY.csv (only added rows allowed).
set -u
R=/home/jin/wt_v4_w08; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
cd $R || exit 1
for m in ras iid; do
  $PY scripts_project/v4_industry.py --anchor-mode $m --work /home/jin/v4w08/work_out_$m > /home/jin/v4w08/out_$m.log 2>&1 || { tail -30 /home/jin/v4w08/out_$m.log; exit 1; }
done
grep -h asean_T_v2 research_inputs/industry_v4/out_*/V4_SWITCHES.json
cp research_inputs/registry_v5/DATA_REGISTRY.csv /home/jin/v4w08/DATA_REGISTRY_before.csv
$PY scripts_project/v4_registry.py || exit 1
$PY scripts_project/d1_registry.py > /home/jin/v4w08/d1_registry.log 2>&1 || { tail -20 /home/jin/v4w08/d1_registry.log; exit 1; }
tail -3 /home/jin/v4w08/d1_registry.log | cut -c1-300
$PY - <<'EOF'
import pandas as pd
a = pd.read_csv("/home/jin/v4w08/DATA_REGISTRY_before.csv", dtype=str, keep_default_na=False).set_index("param_id")
b = pd.read_csv("/home/jin/wt_v4_w08/research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
gone = sorted(set(a.index) - set(b.index)); new = sorted(set(b.index) - set(a.index))
common = sorted(set(a.index) & set(b.index))
changed = [p for p in common if not a.loc[p].equals(b.loc[p])]
print("rows before", len(a), "after", len(b), "removed", len(gone), "added", len(new), "changed", len(changed), changed[:10])
print("added prefixes", sorted({p.split("_")[0] + "_" + p.split("_")[1] for p in new}))
EOF
git status --short research_inputs/registry_v5 | head
