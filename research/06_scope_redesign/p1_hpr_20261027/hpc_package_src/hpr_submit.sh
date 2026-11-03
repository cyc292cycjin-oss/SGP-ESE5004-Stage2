#!/bin/bash
# HPR step E (HPC_OPERATOR_GUIDE.md; RUN_PLAN_HPC 3-4, 6): ONE command submits the formal jobs in order - F1, F2 (depend=after:F1), batch
# (depend=afterany:F1:F2) - and echoes the job ids. V3 HPC (RUN_PLAN_HPC_V3.md 4): the jobs and dependencies of pbs/HPC_PLAN.txt - F1, F2 (after:F1), F3 (afterany:F1),
# F4 (afterany:F2), batch (afterany:F3:F4); refused while the package limits are PROPOSED. Only after 2026-11-02 17:00 SGT, after the smoke passed and when the login banner shows no new
# maintenance overlapping the run (the operator confirms with --motd-checked).
#   bash hpc/hpr_submit.sh --auth-file HPR_AUTH.txt --motd-checked [--resume] [--dry-run]
#   --auth-file  the user's authorisation text (one file, plain text, no host / account / licence content); copied to <package>/HPR_AUTH.txt (mode 600)
#   --resume     allowed only to resubmit after an interruption into the SAME runs/batch4 (an ended run is skipped by the runner, a started-not-ended
#                run is STOP_SAFE:INTERRUPTED - RUN_PLAN_HPC 6); without --resume an existing runs/batch4 refuses
#   --dry-run    V3 HPC (review item 1; HPC_OPERATOR_GUIDE_V3 step c2): nothing is written, copied or submitted and qsub is never called - every check below runs, a
#                check that would refuse a real submission prints "DRY-RUN NOTE: ... - a real submission would be refused" instead, the qsub commands are printed with
#                placeholder job ids (F1_JOBID, ...) and the last line is DRY_RUN_OK; a broken package (plan, job scripts, dependency order) still refuses (exit 2)
# Refusals (exit 2, nothing submitted): a test hook / dry-run switch in this shell, no --motd-checked, missing authorisation, smoke not passed,
# runs/batch4 present without --resume, a STOP / STOP_SAFE present in runs/batch4 (the user resolves it first), a start lock directory left in runs/batch4
# (review item 6), repo commit != COMMIT, licence file missing / not 600, job scripts missing.
set -u
PKG="$(cd "$(dirname "$0")/.." && pwd)"; cd "$PKG" || exit 2
AUTHF=""; MOTD=0; RESUME=0; DRYRUN=0; NOTES=0
while [ $# -gt 0 ]; do case "$1" in --auth-file) AUTHF="$2"; shift 2;; --motd-checked) MOTD=1; shift;; --resume) RESUME=1; shift;; --dry-run) DRYRUN=1; shift;; *) echo "unknown argument $1"; exit 2;; esac; done
refuse() { if [ $DRYRUN = 1 ]; then echo "DRY-RUN NOTE: $1 - a real submission would be refused"; NOTES=$((NOTES + 1)); else echo "REFUSED: $1"; exit 2; fi; }   # a check of the submission
broken() { echo "REFUSED: $1"; exit 2; }   # a broken package: refused in the dry run too
HOOKS="ALLOW_UNREGISTERED BUILD_ONLY POST_ONLY DRY TRUNCATE SOLVE_CMD SPLIT_CMD VA_CMD C1_CMD M12_CMD M12A_CMD G6_CMD SUM_CMD PACK_CMD LEDGER_CMD WALL_CAP_S GUROBI_TIME_LIMIT_S LICENCE_GAP_S GRACE_S MONITOR_S POST_TIMEOUT_S PACK_TIMEOUT_S SOLVE_MODE P1_WINDOW_S P1_THRESHOLD P1_MIN_CORES MEMORY_STOP_FRACTION PROJECTION_FRACTION BUILD_TIMEOUT_S ASSIGN_TIMEOUT_S POST_MEM_NEED_GIB WAIT_START_MAX_S MEM_MEASURE CGROUP_ROOT RUN_DIR CORES MEM_QUOTA_GIB WAIT_START_OF REPO NETS HPR_RUN_ROOT HPR_DRY_TRUNCATE HPR_LOCAL_DRILL"
bad=""; for k in $HOOKS $(compgen -A variable | grep -E '^FAKE_'); do [ -z "${!k:-}" ] || bad="$bad $k"; done
[ -z "$bad" ] || refuse "unset before submitting:$bad"
[ $MOTD = 1 ] || refuse "confirm that the login banner shows NO new maintenance overlapping the next ~11 days, then add --motd-checked (RUN_PLAN_HPC 6)"
AUTHPAT="wls(acces[s]|secre[t])|license[i]d|passw(or[d]|[d])"   # pattern written so that this file itself does not match a key-name scan
if [ -n "$AUTHF" ] && [ -s "$AUTHF" ]; then
  if [ $DRYRUN = 1 ]; then grep -qiE "$AUTHPAT" "$AUTHF" && refuse "the authorisation text must not contain licence or password words"
  else
    [ "$(readlink -f "$AUTHF")" = "$PKG/HPR_AUTH.txt" ] || cp "$AUTHF" "$PKG/HPR_AUTH.txt"; chmod 600 "$PKG/HPR_AUTH.txt"
    grep -qiE "$AUTHPAT" "$PKG/HPR_AUTH.txt" && { echo "REFUSED: the authorisation text must not contain licence or password words"; rm -f "$PKG/HPR_AUTH.txt"; exit 2; }
  fi
else refuse "--auth-file FILE (the user authorisation text) is required (step D1 writes HPR_AUTH.txt)"; fi
S="$PKG/runs/smoke56/SMOKE_STATUS.txt"; [ -f "$S" ] && grep -q "^SMOKE_RESULT:PASS" "$S" || refuse "the smoke job has not passed ($S: SMOKE_RESULT:PASS missing) - step D first"
[ "$(cat repo/.package_commit 2>/dev/null)" = "$(cat COMMIT)" ] || refuse "./repo is not the package commit $(cat COMMIT) (step C install job / preflight sha)"
LIC=${GRB_LICENSE_FILE:-$HOME/.gurobi/gurobi.lic}; [ -f "$LIC" ] && [ "$(stat -c %a "$LIC")" = 600 ] || refuse "licence file missing or not mode 600 at $LIC (step B)"
# the formal and batch jobs with their dependencies, in registration order, from pbs/HPC_PLAN.txt (= b4_batch4.py hpc-plan, written by hpc/make_pbs.sh):
# v2 F1, F2 (after:F1), batch (afterany:F1:F2); V3 HPC (RUN_PLAN_HPC_V3.md 4) F1, F2 (after:F1), F3 (afterany:F1), F4 (afterany:F2), batch (afterany:F3:F4)
[ -f pbs/HPC_PLAN.txt ] || broken "pbs/HPC_PLAN.txt missing (hpc/make_pbs.sh)"
ST=$(grep '^STATUS|' pbs/HPC_PLAN.txt | cut -d'|' -f2); [ -z "$ST" ] || [ "$ST" = REGISTERED ] || refuse "the limits of the package are $ST (RUN_PLAN_HPC_V3.md section 2) - nothing is submitted before the reviewer and the user registered them"
ORDER=(); while IFS='|' read -r _ key name _ _ _ _ mode _ depends _; do case "$mode" in formal|batch) ORDER+=("$key|$name|$depends");; esac; done < <(grep '^JOB|' pbs/HPC_PLAN.txt)
[ ${#ORDER[@]} -ge 3 ] || broken "pbs/HPC_PLAN.txt lists ${#ORDER[@]} formal / batch jobs"
for x in "${ORDER[@]}"; do IFS='|' read -r key name dep <<< "$x"; [ -f "pbs/$name.pbs" ] || broken "pbs/$name.pbs missing (hpc/make_pbs.sh)"; done
if [ -d runs/batch4 ]; then
  [ $RESUME = 1 ] || refuse "runs/batch4 exists - a formal RUN_DIR is used once; --resume only to continue after an interruption (RUN_PLAN_HPC 6)"
  { [ -f runs/batch4/STOP ] || [ -f runs/batch4/STOP_SAFE ]; } && refuse "runs/batch4 holds STOP / STOP_SAFE - the user resolves it first (a resource restart is a NEW RUN_DIR with authorisation)"
  [ -d runs/batch4/.gurobi_start_lock ] && refuse "runs/batch4/.gurobi_start_lock exists (owner: $(cat runs/batch4/.gurobi_start_lock/owner 2>/dev/null || echo unknown)) - a runner may still hold it or a killed job left it; with no job of this package in qstat the reviewer decides (HPC_OPERATOR_GUIDE_V3 H3)"
  for d in runs/batch4/F*; do [ -d "$d" ] || continue; c=$(cat "$d/.cond" 2>/dev/null); case "$c" in build_only|split_built|stopped_before_solve) refuse "$d holds a dry-run leftover";; esac; done
fi
command -v qsub > /dev/null 2>&1 || refuse "qsub not found (login node?)"
declare -A JID; LINE="SUBMITTED:utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"; QUEUED=""
for x in "${ORDER[@]}"; do
  IFS='|' read -r key name dep <<< "$x"; W=()
  if [ -n "$dep" ]; then t=${dep%%:*}; ids=""; for k in $(echo "${dep#*:}" | tr ':' ' '); do [ -n "${JID[$k]:-}" ] || broken "$key depends on $k, not submitted before it (pbs/HPC_PLAN.txt order)"; ids="$ids:${JID[$k]}"; done; W=(-W "depend=$t$ids"); fi
  if [ $DRYRUN = 1 ]; then echo "DRY-RUN: qsub ${W[*]:-}${W[*]:+ }pbs/$name.pbs"; JID[$key]="${key}_JOBID"; continue; fi
  id=$(qsub ${W[@]+"${W[@]}"} "pbs/$name.pbs") || { if [ -n "$QUEUED" ]; then echo "qsub $key failed - already queued:$QUEUED (qdel them if you do not want them alone)"; else echo "qsub $key failed - nothing submitted; fix the qsub error and run this command again"; fi; exit 1; }
  JID[$key]=$id; QUEUED="$QUEUED $key=$id"; LINE="$LINE:$key=$id"
  [ -d runs/batch4 ] || mkdir -p runs/batch4   # created only after the first job is queued (review F-11: a failed first qsub must not block the retry)
  echo "$key job id: $id${dep:+   (depend=$dep)}"
done
if [ $DRYRUN = 1 ]; then echo "DRY_RUN_OK: nothing submitted (bash ${BASH_VERSION}; ${#ORDER[@]} jobs; $NOTES check(s) above would refuse a real submission)"; exit 0; fi
echo "$LINE:resume=$RESUME" | tee -a runs/batch4/SUBMITTED.txt
echo "F2 starts after F1 started; its Gurobi process waits for F1's Gurobi start + 330 s. F3 / F4 (when in the plan) start after F1 / F2 ended; every Gurobi start takes the start lock (>= 330 s after any other start or end, < 2 other sessions). The batch job runs after all runs ended."
echo "monitor: bash hpc/hpr_status.sh"
