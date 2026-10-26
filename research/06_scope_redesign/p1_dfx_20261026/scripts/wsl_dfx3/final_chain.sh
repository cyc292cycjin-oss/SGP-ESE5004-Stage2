#!/bin/bash
# DFX v3: after the affected stand-in tests pass - commit the fix + drafts, second dry run (new dir), second package build, then the full test suite.
set -u
D=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026
rm -f $D/evidence/tests/full.log
[ -d $D/evidence/package ] && [ ! -d $D/evidence/package_superseded_5405e477 ] && mv $D/evidence/package $D/evidence/package_superseded_5405e477
[ -d $D/evidence/dry_run ] && [ ! -d $D/evidence/dry_run_5405e477 ] && mv $D/evidence/dry_run $D/evidence/dry_run_5405e477
echo "== commit"; bash /home/jin/dfx3/commit.sh /home/jin/dfx3/msg_f6fix.txt 2>&1 | tail -4 || exit 1
echo "== dry run v8b"; bash /home/jin/dfx3/dry_run_v8.sh dry_run_v8b 2>&1 | grep -v -E "UserWarning|parser.parse|PROJ" | tail -25
echo "== package v8 (second build)"; bash /home/jin/dfx3/package_v8b.sh dry_run_v8b 2>&1 | grep -v -E "UserWarning|parser.parse"
echo "== full test suite"; bash /home/jin/dfx3/tests_full.sh
