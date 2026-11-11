#!/bin/bash
# 只读：估算新 worktree 的体积（以 W14 worktree 为参照，排除 results_project 与未跟踪文件）
set -u
cd /home/jin/wt_v4_w14 || exit 2
echo "== du wt_v4_w14 total"; du -sh . 2>/dev/null
echo "== du by top dir"; du -sh ./* 2>/dev/null | sort -h | tail -12
echo "== tracked bytes at 26c2e47d"
git ls-tree -r -l 26c2e47d025fdd4e46cb278718d93aeddabbe984 | awk '{s+=$4} END {printf "%d bytes, %.1f MB\n", s, s/1e6}'
echo "== results_project kind"; ls -la results_project | head -20
