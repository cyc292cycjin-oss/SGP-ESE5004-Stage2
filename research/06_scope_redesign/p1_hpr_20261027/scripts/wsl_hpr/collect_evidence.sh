#!/bin/bash
# HPR: copy the evidence of this step into the deliverable folder (worktree) - tests, H4 drill (status files, scrubbed logs, receipts, comparison), dry run,
# package manifest / sums / logs, consistency, leak scan. Gurobi logs are copied scrubbed only; LP / solution arrays and networks never.
set -u
WT=/home/jin/wt_hpr_20261027; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; R=$MAIN/results_project/hpr
E=$WT/research/06_scope_redesign/p1_hpr_20261027/evidence; mkdir -p $E/tests $E/h4 $E/dry_run $E/package $E/leak_scan
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'
cp $R/tests/*.log $E/tests/ 2>/dev/null
# H4 drill
H=$R/h4/runs/smoke56
if [ -d "$H" ]; then
  for f in STATUS.txt PBS_JOBS.txt SMOKE_STATUS.txt BATCH4_SUMMARY.json BATCH4_SUMMARY.md BATCH_REFERENCE.json BASE_CHECK_F1.json BASE_CHECK_F2.json; do [ -f $H/$f ] && cp $H/$f $E/h4/; done
  cp $R/h4/H4_DRILL_STATUS.txt $R/h4/H4_DRILL.json $R/h4/smoke56_job.out $E/h4/ 2>/dev/null
  for rid in F1 F2; do
    d=$H/$rid; mkdir -p $E/h4/$rid/split $E/h4/$rid/m12_owen
    for f in RUN.json SOLVE_RECEIPT.json V6_ACCEPTANCE.json V6_ACCEPTANCE_PROVISIONAL.json PRECISION.json STOP_CLASS.json LEDGER_IDENTITY.json COUNTRY_COST_LEDGER.csv ALLOCATION.json VIOLATIONS.json INTERIOR_CHECKS.json; do [ -f $d/$f ] && cp $d/$f $E/h4/$rid/; done
    for f in split/SPLIT_BUILD.json split/SPLIT_SOLVE.json; do [ -f $d/$f ] && cp $d/$f $E/h4/$rid/split/; done
    [ -f $d/m12_owen/OWEN.json ] && cp $d/m12_owen/OWEN.json $d/m12_owen/OWEN_REGRADE_BATCH_REFERENCE.json $E/h4/$rid/m12_owen/ 2>/dev/null
    [ -f $d/gurobi.linopy.log ] && grep -viE "$SCRUB" $d/gurobi.linopy.log > $E/h4/$rid/gurobi_log_scrubbed.txt
    for f in p1 p2 p3; do [ -f $d/$f.err ] && grep -A 30 "Command being timed" $d/$f.err | grep -viE "$SCRUB" > $E/h4/$rid/${f}_time.txt; done
    [ -f $H/MONITOR_$rid.csv ] && cp $H/MONITOR_$rid.csv $E/h4/$rid/
    ls $H/preflight_*${rid}* > /dev/null 2>&1 && cp $H/preflight_*${rid}* $E/h4/ 2>/dev/null
  done
  cp $H/preflight_*.txt $E/h4/ 2>/dev/null
fi
# dry run
D=$R/dry_run_v9
if [ -d "$D" ]; then
  cp $D/DRYRUN_STATUS.txt $D/REFUSALS.txt $D/preflight_*.txt $D/build_only_job.out $E/dry_run/ 2>/dev/null
  [ -d $D/runs/build_only_f1 ] && { cp $D/runs/build_only_f1/BUILD_ONLY_STATUS.txt $D/runs/build_only_f1/STATUS.txt $D/runs/build_only_f1/PBS_JOBS.txt $E/dry_run/ 2>/dev/null; cp $D/runs/build_only_f1/F1/BUILD_CHECK.json $D/runs/build_only_f1/F1/RUN.json $E/dry_run/ 2>/dev/null; }
  mkdir -p $E/dry_run/refusals; for d in $D/refusals/*/; do n=$(basename $d); [ -f $d/out.txt ] && cp $d/out.txt $E/dry_run/refusals/$n.txt; done; cp $D/refusals/*.txt $E/dry_run/refusals/ 2>/dev/null
fi
# package v9
P=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_hpr_20261027/hpc_package
[ -d "$P" ] && { cp $P/SHA256SUMS $P/HPC_PACKAGE_MANIFEST.json $P/COMMIT $E/package/; cp $P/pbs/*.pbs $P/pbs/MAKE_PBS.log $P/pbs/HPC_PLAN.txt $E/package/ 2>/dev/null; cp $R/package/*.log $E/package/ 2>/dev/null; }
cp $R/CONSISTENCY.json $R/CONSISTENCY.txt $E/ 2>/dev/null
cp $R/leak_scan/HPR_LEAK_SCAN.json $R/leak_scan/*.txt $E/leak_scan/ 2>/dev/null
# never licence-like content in the evidence folder (pattern file outside the repository; counts only)
PF=/home/jin/.dfx_leak_patterns
if [ -r "$PF" ]; then pat=$(grep -v '^#' "$PF" | grep -E '^key=' | cut -d= -f2-); n=$(grep -rIlE "$pat" $E 2>/dev/null | wc -l); echo "licence-like hits in evidence: $n"; fi
du -sh $E; find $E -type f | wc -l
