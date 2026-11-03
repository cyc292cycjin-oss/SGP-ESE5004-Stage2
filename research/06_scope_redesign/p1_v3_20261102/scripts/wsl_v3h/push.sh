#!/bin/bash
cd /home/jin/wt_v3_hpc
timeout 15 bash -c 'exec 3<>/dev/tcp/github.com/443' 2>/dev/null && echo "github reachable" || { echo "NO ROUTE to github from WSL"; exit 3; }
git push -u origin codex/v3-hpc-20261104 2>&1 | tail -3
git ls-remote origin refs/heads/codex/v3-hpc-20261104
