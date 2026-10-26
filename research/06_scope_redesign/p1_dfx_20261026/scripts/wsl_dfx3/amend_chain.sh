#!/bin/bash
# DFX v3 amendment: third dry run (new dir) at the amendment commit, package v8 rebuilt (second build moved aside), local preflight sections.
set -u
cd /home/jin/wt_dfx_v3_20261026 || exit 1
echo "HEAD=$(git rev-parse --short HEAD) dirty=$(git status --porcelain --untracked-files=no | wc -l)"
echo "== dry run v8c"; bash /home/jin/dfx3/dry_run_v8.sh dry_run_v8c 2>&1 | grep -v -E "UserWarning|parser.parse|PROJ" | tail -22
echo "== package v8 (third build)"; bash /home/jin/dfx3/package_v8b.sh dry_run_v8c 2>&1 | grep -v -E "UserWarning|parser.parse"
