#!/bin/bash
# M12b 前置核对（只读）
set -u
echo "=== worktrees"
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model && git worktree list
for wt in /home/jin/wt_m08b_20261021 /home/jin/wt_m12_20261021; do
  echo "=== $wt"
  cd "$wt" || continue
  git branch --show-current
  git log --oneline -n 12 --format='%h %ad %s' --date=iso
  git status --short | head -n 30
done
echo "=== ec80668f"
cd /home/jin/wt_m08b_20261021 && git show --stat --format='%H %ad%n%s%n%b' --date=iso ec80668f | head -n 60
echo "=== branches containing ec80668f"
git branch -a --contains ec80668f
echo "=== gurobi processes"
ps -eo pid,etime,cmd | grep -E '[g]urobi|[s]2_solve' || echo none
echo "=== m08b results"
ls -la /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/ 2>/dev/null
echo "=== m12_local"
ls -la /home/jin/m12_local/ 2>/dev/null
