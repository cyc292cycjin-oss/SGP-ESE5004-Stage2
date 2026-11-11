#!/bin/bash
# 只读：research/ 体积构成、代码与测试对 research/ 的引用、26c2e47d..ac75354c 的改动范围
set -u
cd /home/jin/wt_v4_w14 || exit 2
C=26c2e47d025fdd4e46cb278718d93aeddabbe984
echo "== research/ top"; du -sh research/* 2>/dev/null | sort -h | tail -8
echo "== research/06_scope_redesign largest"; du -sh research/06_scope_redesign/* 2>/dev/null | sort -h | tail -10
echo "== tracked research bytes"; git ls-tree -r -l $C research | awk '{s+=$4} END {printf "%.1f MB\n", s/1e6}'
echo "== tracked research/06 bytes"; git ls-tree -r -l $C research/06_scope_redesign | awk '{s+=$4} END {printf "%.1f MB\n", s/1e6}'
echo "== code/tests referencing research/ paths (count by file)"
grep -rlE "\"research/|'research/|/ \"research\"|research_dir|REPO / \"research\"|ROOT / \"research\"" scripts_project tests configs Snakefile 2>/dev/null | head -30
echo "== diff stat 26c2e47d..ac75354c"; git diff --stat $C ac75354c | tail -5
git diff --name-only $C ac75354c | grep -v '^research/' | head
