#!/bin/bash
set -u
WT=/home/jin/wt_v4_fable; BR=codex/v4-fable-w08-20261107
cd $WT || exit 1
git push -u origin $BR 2>&1 | tail -3
echo "remote: $(git ls-remote origin refs/heads/$BR | cut -c1-40)  local: $(git rev-parse HEAD)"
