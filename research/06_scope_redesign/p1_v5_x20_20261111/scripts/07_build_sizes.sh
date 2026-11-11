#!/bin/bash
# 只读：W14 / D2c 构建产物与冒烟目录的体积（B 段 D 盘占用估算依据）
set -u
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project
for d in v4w14 v4d2c; do
  echo "== $d"; du -sh "$R/$d" 2>/dev/null
  find "$R/$d" -maxdepth 4 \( -name "*.nc" -o -name "*.log" -o -name "*.json" \) -size +1M -printf "%p %s\n" 2>/dev/null | head -20
  du -sh "$R/$d"/* 2>/dev/null | sort -h | tail -8
done
echo "== assembly_v1 / s1 (symlink targets)"; du -sh "$R/assembly_v1" "$R/s1" 2>/dev/null
echo "== cutout"; ls -la /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/cutouts/asean_zenodo_20325289/ 2>/dev/null
echo "== W14 scratch"; du -sh /home/jin/v4w14 2>/dev/null; ls /home/jin/v4w14 2>/dev/null | head -30
