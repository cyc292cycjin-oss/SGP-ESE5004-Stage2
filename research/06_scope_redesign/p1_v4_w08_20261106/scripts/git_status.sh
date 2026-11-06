#!/bin/bash
# W08: worktree status from WSL git (Windows git over UNC reports CRLF / mode noise)
cd /home/jin/wt_v4_w08 || exit 1
git status --short | head -40
echo "N=$(git status --short | wc -l)"
