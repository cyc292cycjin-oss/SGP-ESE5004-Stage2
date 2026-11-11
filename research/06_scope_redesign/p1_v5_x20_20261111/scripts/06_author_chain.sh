#!/bin/bash
# 只读：作者链 pypsa-asean 的 busmap / linemap / base_network 等中间产物是否在本地（用于 ②2 走廊精确重算）
set -u
A=/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean
echo "== resources dirs"; ls "$A/resources" 2>/dev/null
for d in "$A"/resources/*/; do
  echo "== $d"; ls "$d" | head -40
done
echo "== busmap / linemap files"
find "$A/resources" -maxdepth 3 \( -iname "*busmap*" -o -iname "*linemap*" -o -iname "base_network*" -o -iname "elec_s*" \) -printf "%p %s\n" 2>/dev/null | head -40
echo "== osm-plus-prebuilt in research_model data"
ls -la /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/data/osm-plus-prebuilt 2>/dev/null; ls /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/data/osm-plus-prebuilt/* 2>/dev/null | head
echo "== networks in author results"; find "$A/results" -maxdepth 3 -name "*.nc" -printf "%p %s\n" 2>/dev/null | head -20
echo "== snakemake / config of author chain"; ls "$A" | head -40
