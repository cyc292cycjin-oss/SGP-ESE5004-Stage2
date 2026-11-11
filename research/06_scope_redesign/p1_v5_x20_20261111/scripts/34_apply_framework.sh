#!/bin/bash
# X20 B 框架提交：v5_common.py 复制进 worktree，baseline.yaml 第 533 行后插入 v5 开关块（enabled false）
set -eu
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; WT=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
cd $WT
cp $D/x20_src/scripts_project/v5_common.py scripts_project/v5_common.py; sed -i 's/\r$//' scripts_project/v5_common.py; chmod 644 scripts_project/v5_common.py
grep -q '^    v5:' configs/research/baseline.yaml && { echo "v5 block already present"; exit 1; }
[ "$(sed -n 533p configs/research/baseline.yaml | awk '{print $1}')" = "source_band_basis:" ] || { echo "line 533 is not source_band_basis"; exit 1; }
tr -d '\r' < $D/x20_src/baseline_v5_block.yaml > /tmp/x20_v5_block.yaml
sed -i '533r /tmp/x20_v5_block.yaml' configs/research/baseline.yaml; rm -f /tmp/x20_v5_block.yaml
$PY - <<'PY'
import yaml, sys
sys.path.insert(0, "scripts_project")
b = yaml.safe_load(open("configs/research/baseline.yaml"))
v5 = b["research"]["demand"]["v5"]; print("v5 keys", len(v5), "enabled", v5["enabled"], "biomass key next:", list(b["research"])[list(b["research"]).index("demand") + 1])
import v5_common as V
print("V5_MAIN keys equal:", set(v5) == set(V.V5_MAIN), "values equal:", all(v5[k] == V.V5_MAIN[k] for k in V.V5_MAIN if k != "enabled"))
PY
git diff --stat
