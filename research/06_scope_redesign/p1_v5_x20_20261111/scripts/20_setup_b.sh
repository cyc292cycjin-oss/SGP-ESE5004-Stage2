#!/bin/bash
# X20 B 段准备：稀疏检出 -> 完整检出（决策 246 Q9 (a)）；finance_v5 被忽略输入；results_project 链接（构建与测试产物在 D 盘）；本步目录文件模式 100644
set -u
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
WT=/home/jin/wt_v5_x20
D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
STEP=research/06_scope_redesign/p1_v5_x20_20261111
echo "== date"; date '+%Y-%m-%d %H:%M:%S %Z'
echo "== df / before"; df -h / | tail -1
cd "$WT" || exit 2
[ "$(git branch --show-current)" = "asean/v5-x20-20261111" ] || { echo "wrong branch"; exit 3; }
git sparse-checkout disable
echo "== du worktree after full checkout"; du -sb "$WT"
git status --short | head -5; echo "(status lines: $(git status --short | wc -l))"
# finance_v5 被忽略的两个输入（只供 test_s4c_0 使用，不提交）
for f in COUNTRY_WACC_PUBLIC_SOURCES.csv DISCOUNT_RATE_IN_USE.csv; do
  if [ -e "$MAIN/research_inputs/finance_v5/$f" ] && [ ! -e "research_inputs/finance_v5/$f" ]; then cp "$MAIN/research_inputs/finance_v5/$f" "research_inputs/finance_v5/$f" && echo "copied $f"; fi
done
# 构建输入链接（只读）与 v5 产物链接（D 盘）
mkdir -p results_project "$D/builds" "$D/tmp" "$D/pycache" "$D/pytest_tmp" "$D/trunc56" "$D/smoke56" "$D/downloads/osm" "$D/downloads/ngcp"
for d in assembly_v1 s1; do [ -e "results_project/$d" ] || ln -s "$MAIN/results_project/$d" "results_project/$d"; done
[ -e results_project/v5x20 ] || ln -s "$D/builds" results_project/v5x20
ls -la results_project
# 本步目录文件模式改回 100644（A 段从 /mnt/d 复制时带上了 755）
chmod 644 "$STEP"/*.md "$STEP"/*.csv "$STEP"/*.txt "$STEP"/scripts/* "$STEP"/logs/* "$STEP"/evidence/*
git add --chmod=-x "$STEP"
echo "== staged mode changes"; git diff --cached --summary | head -5; echo "(mode lines: $(git diff --cached --summary | wc -l))"
echo "== df / after"; df -h / | tail -1
echo "== free"; free -b | head -2
