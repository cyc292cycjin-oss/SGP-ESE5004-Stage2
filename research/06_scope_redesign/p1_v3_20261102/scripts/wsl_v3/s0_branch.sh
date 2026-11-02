#!/bin/bash
# V3 section 0: create branch + worktree from the HPR head, results folder in main checkout
set -e
R=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
W=/home/jin/wt_v3_20261102
cd "$R"
git worktree add -b codex/v3-20261102 "$W" 0a20aefd8dc4ff8bd4ecb1c60c8b36f874eada71 2>&1 | tail -3
mkdir -p "$R/results_project/v3"
cd "$W"
echo "== head"; git log -1 --format='%h %s' | cut -c1-120
git status --short | head
git branch --show-current
echo "== push"
git push -u origin codex/v3-20261102 2>&1 | tail -4
echo "== remote head"
git ls-remote origin refs/heads/codex/v3-20261102
echo "== worktree size"
du -sh "$W"
