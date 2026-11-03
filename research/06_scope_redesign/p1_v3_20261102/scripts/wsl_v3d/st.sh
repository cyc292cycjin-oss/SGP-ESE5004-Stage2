#!/bin/bash
# V3 supplement 07: read-only state check (worktree head, tracked changes, solver / build processes, disk)
W=/home/jin/wt_v3_20261102
cd "$W" || exit 2
echo "== branch / head"; git rev-parse --abbrev-ref HEAD; git log --oneline -5 | cut -c1-110
echo "== remote head"; git rev-parse origin/codex/v3-20261102 2>/dev/null
echo "== tracked changes"; git status --short --untracked-files=no | head -20
echo "== untracked under research/06 v3"; git status --short research/06_scope_redesign/p1_v3_20261102 | head -10
echo "== processes"; ps -eo pid,etime,args | grep -E "s2_solve|gurobi|python|snakemake" | grep -v grep | grep -v "ps -eo" | cut -c1-150
echo "== disk"; df -h /home/jin /mnt/d 2>/dev/null | tail -2
du -sh /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3 2>/dev/null
echo "== python"; ls -la /home/jin/miniforge3/envs/pypsa-earth/bin/python
