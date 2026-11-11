#!/bin/bash
# X20：注册表链（同 D2c run_registry.sh 的顺序）：v4_registry（含 baseline.yaml 的 SHA256）-> v4_d1 -> v4_d2a -> v4_d2b -> v4_d2c -> [v5_x20] -> d1_registry；
# 与 HEAD 的 DATA_REGISTRY.csv 逐行比较。用法：36_registry_chain.sh <标签>；工作目录在 D 盘 cache/registry/<标签>。
set -u
TAG=${1:?tag}
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; T=$D/cache/registry/$TAG; LOG=$D/logs/36_registry_$TAG.log
export PYTHONHASHSEED=0
mkdir -p $T
cd $R || exit 1
{
echo "HEAD $(git rev-parse HEAD) baseline.yaml sha256 $(sha256sum configs/research/baseline.yaml | cut -c1-64)"
git show HEAD:research_inputs/registry_v5/DATA_REGISTRY.csv > $T/DATA_REGISTRY_head.csv
$PY scripts_project/v4_registry.py > $T/v4_registry.log 2>&1 || { tail -20 $T/v4_registry.log; exit 1; }
for s in v4_d1 v4_d2a v4_d2b v4_d2c; do $PY scripts_project/${s}_registry.py > $T/$s.log 2>&1 || { tail -20 $T/$s.log; exit 1; }; done
if [ -e scripts_project/v5_x20_registry.py ]; then
  for f in v5_x20 v5_x20_corrections; do [ -e research_inputs/registry_v5/fragments/$f.csv ] || { head -1 research_inputs/registry_v5/fragments/v4_d2b.csv > research_inputs/registry_v5/fragments/$f.csv; echo "placeholder $f.csv (header only; written below by v5_x20_registry.py)"; }; done
  $PY scripts_project/v5_x20_registry.py > $T/v5_x20.log 2>&1 || { tail -20 $T/v5_x20.log; exit 1; }
fi
$PY scripts_project/d1_registry.py > $T/d1_registry.log 2>&1 || { tail -20 $T/d1_registry.log; exit 1; }
tail -2 $T/d1_registry.log | cut -c1-300
$PY - "$T/DATA_REGISTRY_head.csv" "$R/research_inputs/registry_v5/DATA_REGISTRY.csv" <<'P'
import sys
import pandas as pd
a = pd.read_csv(sys.argv[1], dtype=str, keep_default_na=False).set_index("param_id")
b = pd.read_csv(sys.argv[2], dtype=str, keep_default_na=False).set_index("param_id")
gone = sorted(set(a.index) - set(b.index)); new = sorted(set(b.index) - set(a.index))
common = sorted(set(a.index) & set(b.index))
changed = [p for p in common if not a.loc[p].equals(b.loc[p])]
print("rows before", len(a), "after", len(b), "removed", len(gone), gone, "added", len(new), "changed", len(changed))
for p in changed:
    cols = [c for c in a.columns if a.at[p, c] != b.at[p, c]]
    print("  CHANGED", p, {c: (a.at[p, c][:70], b.at[p, c][:70]) for c in cols})
for p in new:
    print("  NEW", p, b.at[p, "value"], b.at[p, "unit"], b.at[p, "tier"], b.at[p, "status"])
P
echo "== git status research_inputs/registry_v5"; git status --short research_inputs/registry_v5 | head -20
} > $LOG 2>&1
cat $LOG | cut -c1-400
