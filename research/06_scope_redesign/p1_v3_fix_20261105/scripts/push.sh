#!/bin/bash
# Push the fix branch to origin (the project repository) and verify with ls-remote. No force push, no merge.
set -u
cd /home/jin/wt_v3_fix
B=codex/v3-fix-20261105
[ "$(git rev-parse --abbrev-ref HEAD)" = $B ] || { echo "wrong branch"; exit 2; }
git remote get-url origin | sed -E 's#https://[^@]*@#https://#'
git push -u origin $B 2>&1 | tail -5
L=$(git rev-parse HEAD); R=$(git ls-remote origin refs/heads/$B | cut -f1)
echo "local $L"; echo "remote $R"; [ "$L" = "$R" ] && echo PUSH_VERIFIED || echo PUSH_MISMATCH
