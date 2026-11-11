#!/bin/bash
# X20 §3 第 8 步：审阅包（x20_review_zip.py）；泄露扫描模式只经环境变量 X20_LEAK_PATTERNS 传入（由调用方在运行时提供，经 WSLENV 转入），本脚本不含任何模式
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
[ -n "${X20_LEAK_PATTERNS:-}" ] || { echo "X20_LEAK_PATTERNS not set"; exit 2; }
echo "patterns: ${#X20_LEAK_PATTERNS} chars (not printed)"
$PY $D/scripts/x20_review_zip.py "${1:?commit}"
