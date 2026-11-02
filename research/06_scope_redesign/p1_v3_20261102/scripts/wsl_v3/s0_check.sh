#!/bin/bash
# V3 section 0 read-only checks
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
cd "$R" || exit 2
echo "== remotes"; git remote -v
echo "== fetch origin (hpr branch only)"
git fetch origin codex/hpr-20261027 2>&1 | tail -3
echo "== local/remote heads"
git rev-parse --short=8 codex/hpr-20261027 2>/dev/null
git rev-parse --short=8 origin/codex/hpr-20261027 2>/dev/null
git rev-parse 0a20aefd 2>/dev/null
echo "== worktrees"
git worktree list | tail -8
echo "== log 8ed41d97..origin/codex/hpr-20261027 (stat)"
git log --oneline 8ed41d97..origin/codex/hpr-20261027 | head -40
echo "== diff 8ed41d97 head in scripts_project research_inputs configs"
git diff --stat 8ed41d97 origin/codex/hpr-20261027 -- scripts_project research_inputs configs
echo "== all changed paths between 8ed41d97 and head"
git diff --name-status 8ed41d97 origin/codex/hpr-20261027
echo "== existing v3 branch?"
git branch -a | grep -E 'v3-20261102' || echo none
ls -d /home/jin/wt_v3_20261102 2>/dev/null || echo "no worktree dir"
echo "== processes"
ps -eo pid,etime,pcpu,pmem,cmd | grep -E '[g]urobi|[s]2_solve|[s]2_network|[s]nakemake|[m]08|[b]uild_' || echo "no gurobi/build processes"
echo "== disk"
df -h /home/jin | tail -1
df -h /mnt/d | tail -1
free -g | head -2
