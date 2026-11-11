#!/bin/bash
# X20 A 段开工检查：磁盘基线、内存、仓库状态、W14 COMMIT（只读）
set -u
REPO=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
DELIV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111
echo "== date"; date '+%Y-%m-%d %H:%M:%S %Z'
echo "== df -h /"; df -h /
echo "== df -h /mnt/d"; df -h /mnt/d
echo "== du delivery"; du -sb "$DELIV"; du -sh "$DELIV"
echo "== du home"; du -sh /home/jin 2>/dev/null | tail -1
echo "== free"; free -b; free -g
echo "== nproc"; nproc
echo "== processes (python/gurobi/snakemake)"; ps -eo pid,etimes,rss,args | grep -E "python|gurobi|snakemake" | grep -v grep || echo none
echo "== repo"; cd "$REPO" || exit 2
git --no-pager log -1 --format='%H %s'
git status --short | head -20
echo "== commit 26c2e47d"; git cat-file -t 26c2e47d025fdd4e46cb278718d93aeddabbe984 && git --no-pager log -1 --format='%H %ad %s' 26c2e47d025fdd4e46cb278718d93aeddabbe984
echo "== branches containing 26c2e47d"; git branch -a --contains 26c2e47d025fdd4e46cb278718d93aeddabbe984 | head
echo "== existing x20 branch?"; git branch -a | grep -i x20 || echo none
echo "== worktrees"; git worktree list | tail -15
echo "== remotes"; git remote -v | grep origin
