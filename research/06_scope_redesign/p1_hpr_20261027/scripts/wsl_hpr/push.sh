#!/bin/bash
# HPR: push the branch (never force), verify the remote head equals the local head.
cd /home/jin/wt_hpr_20261027 || exit 1
[ "$(git status --porcelain --untracked-files=no | wc -l)" = 0 ] || { echo "tracked changes present - commit first"; exit 2; }
git push -u origin codex/hpr-20261027 2>&1 | tail -5; rc=${PIPESTATUS[0]}
echo "PUSH_EXIT=$rc"
echo "local  $(git rev-parse HEAD)"; echo "remote $(git ls-remote --heads origin codex/hpr-20261027 | cut -f1)"
echo "merges since base: $(git log --merges --oneline 82c32c53..HEAD | wc -l); commits: $(git log --oneline 82c32c53..HEAD | wc -l)"
