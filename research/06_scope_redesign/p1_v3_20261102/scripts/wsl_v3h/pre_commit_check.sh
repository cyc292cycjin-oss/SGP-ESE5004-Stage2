#!/bin/bash
cd /home/jin/wt_v3_hpc
for f in $(git status --porcelain | awk '{print $2}'); do [ -f "$f" ] && { grep -c $'\r' "$f" | sed "s|^|$f CR=|"; }; done
git diff --summary | grep -i mode || echo "no mode changes"
git status --porcelain
