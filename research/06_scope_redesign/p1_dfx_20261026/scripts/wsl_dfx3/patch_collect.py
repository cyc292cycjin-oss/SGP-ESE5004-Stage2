p = "/home/jin/dfx3/collect_evidence.sh"; s = open(p).read()
s = s.replace("cp $MAIN/dry_run_v8/DRY_RUN_DFX.json $MAIN/dry_run_v8/make_package.log $MAIN/dry_run_v8/preflight_local_sections.txt $MAIN/dry_run_v8/preflight_local_resources.txt $MAIN/dry_run_v8/refusals/REFUSALS.txt $D/dry_run/",
              "DR=${1:-dry_run_v8b}; cp $MAIN/$DR/DRY_RUN_DFX.json $MAIN/$DR/make_package.log $MAIN/$DR/preflight_local_sections.txt $MAIN/$DR/preflight_local_resources.txt $MAIN/$DR/refusals/REFUSALS.txt $D/dry_run/")
s = s.replace("for p in full trunc; do cp $MAIN/dry_run_v8/$p/STATUS.txt $D/dry_run/${p}_STATUS.txt; for r in V1 V2; do cp $MAIN/dry_run_v8/$p/$r/BUILD_CHECK.json $D/dry_run/${p}_${r}_BUILD_CHECK.json; done; done",
              "for p in full trunc; do cp $MAIN/$DR/$p/STATUS.txt $D/dry_run/${p}_STATUS.txt; for r in V1 V2; do cp $MAIN/$DR/$p/$r/BUILD_CHECK.json $D/dry_run/${p}_${r}_BUILD_CHECK.json; done; done")
s = s.replace("cp $MAIN/tests/subset.log $MAIN/tests/runner.log $D/tests/ 2>/dev/null; [ -f $MAIN/tests/full.log ] && cp $MAIN/tests/full.log $D/tests/full.log",
              "cp $MAIN/tests/subset.log $MAIN/tests/runner.log $MAIN/tests/affected.log $D/tests/ 2>/dev/null; [ -f $MAIN/tests/full.log ] && cp $MAIN/tests/full.log $D/tests/full.log")
assert "DR=${1:-dry_run_v8b}" in s and "affected.log" in s and "$MAIN/$DR/$p/STATUS.txt" in s
open(p, "w").write(s); print("collect_evidence.sh patched (dry-run dir arg, affected.log)")
