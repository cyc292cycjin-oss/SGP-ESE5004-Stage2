#!/bin/bash
# DFX v3 P10: push the branch (never force), verify the remote head equals the local head.
cd /home/jin/wt_dfx_v3_20261026 || exit 1
[ "$(git status --porcelain --untracked-files=no | wc -l)" = 0 ] || { echo "tracked changes present - commit first"; exit 2; }
git push -u origin codex/dfx-v3-20261026 2>&1 | tail -5; rc=${PIPESTATUS[0]}
echo "PUSH_EXIT=$rc"
echo "local  $(git rev-parse HEAD)"; echo "remote $(git ls-remote --heads origin codex/dfx-v3-20261026 | cut -f1)"
echo "merges since base: $(git log --merges --oneline 55ab07c0..HEAD | wc -l); commits: $(git log --oneline 55ab07c0..HEAD | wc -l)"
