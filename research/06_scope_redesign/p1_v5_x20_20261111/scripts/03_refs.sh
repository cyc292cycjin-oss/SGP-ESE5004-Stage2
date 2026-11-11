#!/bin/bash
# 只读：git 版本、代码/测试对 research/04、05、06 的引用、共享配置现状
set -u
cd /home/jin/wt_v4_w14 || exit 2
git --version
echo "== refs to research/04_model_assembly"; grep -rln "04_model_assembly" scripts_project tests configs scripts Snakefile 2>/dev/null | grep -v retired | head -20
echo "== refs to research/05_baseline_evolution"; grep -rln "05_baseline_evolution" scripts_project tests configs scripts Snakefile 2>/dev/null | grep -v retired | head -20
echo "== refs to research/06_scope_redesign (count)"; grep -rln "06_scope_redesign" scripts_project tests configs scripts Snakefile 2>/dev/null | grep -v retired | wc -l
echo "== shared config extensions/sparse"; git config --show-origin --get-regexp "extensions|sparse|worktree" || echo none
