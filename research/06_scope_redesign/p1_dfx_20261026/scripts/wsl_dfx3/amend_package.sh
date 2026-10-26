#!/bin/bash
# DFX v3 amendment: the package build was refused because documentation edits (made while the dry run ran) dirtied the tracked tree. They live
# under research/ (outside the code archive): stash them, build the package at the dry-run commit 16b209e2, restore them.
set -u
cd /home/jin/wt_dfx_v3_20261026 || exit 1
echo "dirty tracked files:"; git status --porcelain --untracked-files=no
git stash push -q && echo "stashed" || { echo "nothing to stash"; }
echo "HEAD=$(git rev-parse --short HEAD) dirty=$(git status --porcelain --untracked-files=no | wc -l)"
bash /home/jin/dfx3/package_v8b.sh dry_run_v8c 2>&1 | grep -v -E "UserWarning|parser.parse" | grep -E "first build moved|dry run:|build inputs|manifest:|MAKE_PACKAGE_EXIT|^[0-9a-f]{40}$|SHA256SUMS all|PREFLIGHT_LOCAL_EXIT|TimeLimit|modules import|all_equal|no 2920|key_all_equal|PREFLIGHT OK|RESOURCES_LOCAL|SET IN THIS|MIRROR_CHECK_DONE|tracked changes"
git stash pop -q && echo "stash restored: dirty=$(git status --porcelain --untracked-files=no | wc -l)"
