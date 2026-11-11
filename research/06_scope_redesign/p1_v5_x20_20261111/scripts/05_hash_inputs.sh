#!/bin/bash
# X20 A 段：计算 B 段将复用的 X03 / X10 产出的 SHA256，并核对 GWA 下载日志（只读）
set -u
W=/d/ResearchWorkspaces/ASEAN/work
OUT=$W/p1_v5_x20_20261111/evidence
mkdir -p "$OUT"
cd "$W" || exit 2
# 1) GWA：按下载日志逐个核对
awk -F'\t' 'NR>1 {print $7"  p1_v5_x03_renew_20261111/downloads/gwa/"$5}' p1_v5_x03_renew_20261111/downloads/gwa/GWA_DOWNLOAD_LOG.tsv > "$OUT/GWA_SHA256_FROM_LOG.txt"
echo "== GWA check"; sha256sum -c "$OUT/GWA_SHA256_FROM_LOG.txt" | tail -3; echo "gwa_check_exit=${PIPESTATUS[0]}"
# 2) X03 / X10 报告、CSV 与 cache 中 B 段要用的文件
{
  sha256sum p1_v5_x03_renew_20261111/REPORT.md p1_v5_x03_renew_20261111/*.csv p1_v5_x03_renew_20261111/EVIDENCE.json p1_v5_x03_renew_20261111/downloads/gwa/GWA_DOWNLOAD_LOG.tsv
  sha256sum p1_v5_x03_renew_20261111/cache/onwind_cells/* p1_v5_x03_renew_20261111/cache/gwa_lc100/* p1_v5_x03_renew_20261111/cache/onwind_country_class_cf_options.csv p1_v5_x03_renew_20261111/cache/x07_new_hydro_units.csv
  sha256sum p1_v5_x10_checks_20261111/REPORT.md p1_v5_x10_checks_20261111/BUNKER_CARBON_MEMO.md p1_v5_x10_checks_20261111/*.csv p1_v5_x10_checks_20261111/EVIDENCE.json
  sha256sum p1_v5_x10_checks_20261111/cache/*.csv p1_v5_x10_checks_20261111/cache/*.json
} > "$OUT/REUSED_INPUTS_SHA256.txt"
wc -l "$OUT/REUSED_INPUTS_SHA256.txt"
echo "== zip SHA"; cat p1_v5_x03_renew_20261111/REVIEW_ZIP_SHA256.txt p1_v5_x10_checks_20261111/REVIEW_ZIP_SHA256.txt
sha256sum p1_v5_x03_renew_20261111/REVIEW_c6352f89.zip p1_v5_x10_checks_20261111/REVIEW_d0a8cb01.zip
