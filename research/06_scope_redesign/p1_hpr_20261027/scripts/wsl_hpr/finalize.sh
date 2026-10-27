#!/bin/bash
# HPR finalisation in two steps (no solve; run only when no test / solve process is running):
#   bash finalize.sh build   -> commit the document fixes (msg_h7d.txt), rebuild the FINAL package at that commit (shipped-script note), dry run, consistency, leak scan, evidence
#   bash finalize.sh final   -> assemble HPR_REPORT.md (body + RUN_PLAN_HPC.md verbatim appendix), HPR_EVIDENCE.json, placeholder guard, final commit (msg_final.txt), push, mirror to Windows
set -u
WT=/home/jin/wt_hpr_20261027; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
R=$MAIN/results_project/hpr; D=$WT/research/06_scope_redesign/p1_hpr_20261027; W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_hpr_20261027; DIST=$W/hpc_package; S=$R/FINALIZE_STATUS.txt
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" | tee -a "$S"; }
cd "$WT" || exit 1
n=$(ps -eo args= | grep -E '[p]ytest|[s]2_solve\.py|[b]4_split_solve\.py' | wc -l); [ "$n" = 0 ] || { log ABORT "processes running: $n"; exit 4; }
STEP=${1:?build|final}
log START "$STEP:commit=$(git rev-parse HEAD)"
if [ "$STEP" = build ]; then
  bash /home/jin/hpr/commit.sh /home/jin/hpr/msg_h7d.txt 2>&1 | tail -3 | tee -a "$S"
  [ "$(git status --porcelain --untracked-files=no | wc -l)" = 0 ] || { log ABORT "tree not clean after the commit"; exit 2; }
  log DOC_COMMIT "$(git rev-parse HEAD)"
  if [ -d "$DIST" ]; then old=$(cut -c1-8 "$DIST/COMMIT"); rm -rf "$DIST" && log REMOVED_PREVIOUS_BUILD "$old (never uploaded)"; fi
  export H4_PATH_DIFF_OK=1
  export H4_PATH_DIFF_NOTE="Independent review (H7, 2026-10-27) fixes after the H4 drill at be5e49fd: run_batch4.sh --only ignores the other job's run for the post-processing memory condition / thread budget and reads no cgroup file in rss mode (F-07); hpr_job.sh batch gate accepts a run that never started after a halt (F-06), SMOKE_STATUS takes the token-server status from PBS_JOBS.txt (F-04), records OMP_NUM_THREADS / SHELL (F-17), per-job preflight JSON names (F-15); preflight.sh PREFLIGHT_TAG (F-15); make_pbs.sh adds #PBS -S /bin/bash (F-14). The archived code (s2_solve.py, b4_split_solve.py, model, config) is byte-identical to the drill commit; the changed scripts are covered by the stand-in tests of this commit (test_hpr_two_jobs.py, test_b4p_batch4.py) and by the HPC smoke job (step D, real Gurobi, the hard gate of step E)."
  t0=$(date +%s); bash /home/jin/hpr/package_v9.sh "$DIST" > "$R/package_v9_run.log" 2>&1; rc=$?; log PACKAGE "exit=$rc:seconds=$(( $(date +%s) - t0 ))"; grep -E "accepted|REFUSED|manifest:|SHA256SUMS" "$R/package_v9_run.log" | cut -c1-300
  [ $rc = 0 ] || { log ABORT "package failed"; exit 2; }
  t0=$(date +%s); bash /home/jin/hpr/dryrun.sh "$DIST" > "$R/dryrun_run.log" 2>&1; rc=$?; log DRYRUN "exit=$rc:seconds=$(( $(date +%s) - t0 )):$(grep -E '^REFUSALS|^BUILD_ONLY_56' "$R/dry_run_v9/DRYRUN_STATUS.txt" | tr '\n' ' ' | cut -c1-300)"
  $PY research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/hpr_consistency.py --repo "$WT" --plan research/06_scope_redesign/p1_hpr_20261027/RUN_PLAN_HPC.md --runner "$DIST/run_batch4.sh" --preflight "$DIST/preflight.sh" --pbs "$DIST/pbs" --job "$DIST/hpc/hpr_job.sh" --out "$R/CONSISTENCY.json" > "$R/CONSISTENCY.txt" 2>&1; rc=$?
  log CONSISTENCY "exit=$rc:$(tail -1 "$R/CONSISTENCY.txt")"
  bash /home/jin/hpr/leak_scan.sh > "$R/leak_scan_run.log" 2>&1; log LEAK_SCAN "exit=$?"
  $PY -c "
import json; r=json.load(open('$R/leak_scan/HPR_LEAK_SCAN.json'))
print('LEAK: secret_values', r['n_secret_values'], 'clean', r['clean'], 'commits', r['n_commits'], '| hit files:', {t.split('/')[-1]: [h['file'] for h in v['hits']] for t, v in r['targets'].items()}, '| commits with hits:', {k: v['files'] for k, v in r['commits'].items() if v['value_hits'] or v['pattern_hits']})" | tee -a "$S"
  bash /home/jin/hpr/collect_evidence.sh > "$R/collect_evidence.log" 2>&1; log EVIDENCE "exit=$?:$(tail -2 "$R/collect_evidence.log" | tr '\n' ' ')"
  cp "$R/tests/full_rs.log" "$R/tests/full_rs_commit.txt" "$R/tests/full_rs_skips.txt" "$D/evidence/tests/" 2>/dev/null
  $PY -c "
import json; m=json.load(open('$DIST/HPC_PACKAGE_MANIFEST.json')); h=m['h4_drill']
print('MANIFEST', m['commit'], len(m['files']), 'files', m['upload_total_bytes_excluding_this_manifest'], 'B; sums', m['sha256sums_sha256'], '; h4 identical', h['drilled_path_identical_to_package_commit'])" | tee -a "$S"
  sha256sum "$DIST/HPC_PACKAGE_MANIFEST.json" | tee -a "$S"
  log BUILD_DONE "package_commit=$(cat "$DIST/COMMIT")"
fi
if [ "$STEP" = final ]; then
  { cat /home/jin/hpr/report_body.md; echo; echo "---"; echo; echo "## 附录 A：\`RUN_PLAN_HPC.md\` 原文（提交 \`1f62176f\` 登记；H7 后的说明性修订见其头部）"; echo; sed 's/^#/##/' "$D/RUN_PLAN_HPC.md"; } > "$D/HPR_REPORT.md"
  $PY /home/jin/hpr/make_evidence_json.py "$WT" "$D/HPR_EVIDENCE.json" | tee -a "$S"
  for f in HPR_REPORT.md PRE_HPC_CHECKLIST.md INDEPENDENT_REVIEW.md HPC_OPERATOR_GUIDE.md RUN_PLAN_HPC.md HPR_PROGRESS.md; do
    c=$(grep -c "待填\|PLACEHOLDER" "$D/$f"); [ "$c" = 0 ] || log PLACEHOLDER_LEFT "$f:$c"
  done
  grep -q "PLACEHOLDER_LEFT" "$S" && { log ABORT "placeholders left - fix the documents first"; exit 3; }
  bash /home/jin/hpr/commit.sh /home/jin/hpr/msg_final.txt 2>&1 | tail -4 | tee -a "$S"
  bash /home/jin/hpr/push.sh 2>&1 | tee -a "$S"
  bash /home/jin/hpr/sync_work.sh > "$R/sync_work.log" 2>&1; log SYNC "exit=$?:$(tail -1 "$R/sync_work.log")"
  log DONE "head=$(git rev-parse HEAD)"
fi
