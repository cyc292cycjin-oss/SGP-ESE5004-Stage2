#!/bin/bash
# HPR step E (HPC_OPERATOR_GUIDE.md; RUN_PLAN_HPC 3-4, 6): ONE command submits the formal jobs in order - F1, F2 (depend=after:F1), batch
# (depend=afterany:F1:F2) - and echoes the job ids. V3 HPC (RUN_PLAN_HPC_V3.md 4): the jobs and dependencies of pbs/HPC_PLAN.txt - F1, F2 (after:F1), F3 (afterany:F1),
# F4 (afterany:F2), batch (afterany:F3:F4); refused while the package limits are PROPOSED. Only after 2026-11-02 17:00 SGT, after the smoke passed and when the login banner shows no new
# maintenance overlapping the run (the operator confirms with --motd-checked).
#   bash hpc/hpr_submit.sh --auth-file HPR_AUTH.txt --motd-checked [--resume]
#   --auth-file  the user's authorisation text (one file, plain text, no host / account / licence content); copied to <package>/HPR_AUTH.txt (mode 600)
#   --resume     allowed only to resubmit after an interruption into the SAME runs/batch4 (an ended run is skipped by the runner, a started-not-ended
#                run is STOP_SAFE:INTERRUPTED - RUN_PLAN_HPC 6); without --resume an existing runs/batch4 refuses
# Refusals (exit 2, nothing submitted): a test hook / dry-run switch in this shell, no --motd-checked, missing authorisation, smoke not passed,
# runs/batch4 present without --resume, a STOP / STOP_SAFE present in runs/batch4 (the user resolves it first), repo commit != COMMIT, licence file
# missing / not 600, job scripts missing.
set -u
PKG="$(cd "$(dirname "$0")/.." && pwd)"; cd "$PKG" || exit 2
AUTHF=""; MOTD=0; RESUME=0
while [ $# -gt 0 ]; do case "$1" in --auth-file) AUTHF="$2"; shift 2;; --motd-checked) MOTD=1; shift;; --resume) RESUME=1; shift;; *) echo "unknown argument $1"; exit 2;; esac; done
HOOKS="ALLOW_UNREGISTERED BUILD_ONLY POST_ONLY DRY TRUNCATE SOLVE_CMD SPLIT_CMD VA_CMD C1_CMD M12_CMD M12A_CMD G6_CMD SUM_CMD PACK_CMD LEDGER_CMD WALL_CAP_S GUROBI_TIME_LIMIT_S LICENCE_GAP_S GRACE_S MONITOR_S POST_TIMEOUT_S PACK_TIMEOUT_S SOLVE_MODE P1_WINDOW_S P1_THRESHOLD P1_MIN_CORES MEMORY_STOP_FRACTION PROJECTION_FRACTION BUILD_TIMEOUT_S ASSIGN_TIMEOUT_S POST_MEM_NEED_GIB WAIT_START_MAX_S MEM_MEASURE CGROUP_ROOT RUN_DIR CORES MEM_QUOTA_GIB WAIT_START_OF REPO NETS HPR_RUN_ROOT HPR_DRY_TRUNCATE HPR_LOCAL_DRILL"
bad=""; for k in $HOOKS $(compgen -A variable | grep -E '^FAKE_'); do [ -z "${!k:-}" ] || bad="$bad $k"; done
[ -z "$bad" ] || { echo "REFUSED: unset before submitting:$bad"; exit 2; }
[ $MOTD = 1 ] || { echo "REFUSED: confirm that the login banner shows NO new maintenance overlapping the next ~11 days, then add --motd-checked (RUN_PLAN_HPC 6)"; exit 2; }
[ -n "$AUTHF" ] && [ -s "$AUTHF" ] || { echo "REFUSED: --auth-file <file with the user authorisation text> is required"; exit 2; }
[ "$(readlink -f "$AUTHF")" = "$PKG/HPR_AUTH.txt" ] || cp "$AUTHF" "$PKG/HPR_AUTH.txt"; chmod 600 "$PKG/HPR_AUTH.txt"
grep -qiE "wls(acces[s]|secre[t])|license[i]d|passw(or[d]|[d])" "$PKG/HPR_AUTH.txt" && { echo "REFUSED: the authorisation text must not contain licence or password words"; rm -f "$PKG/HPR_AUTH.txt"; exit 2; }   # pattern written so that this file itself does not match a key-name scan
S="$PKG/runs/smoke56/SMOKE_STATUS.txt"; [ -f "$S" ] && grep -q "^SMOKE_RESULT:PASS" "$S" || { echo "REFUSED: the smoke job has not passed ($S: SMOKE_RESULT:PASS missing) - step D first"; exit 2; }
[ "$(cat repo/.package_commit 2>/dev/null)" = "$(cat COMMIT)" ] || { echo "REFUSED: ./repo is not the package commit $(cat COMMIT) (step C install job / preflight sha)"; exit 2; }
LIC=${GRB_LICENSE_FILE:-$HOME/.gurobi/gurobi.lic}; [ -f "$LIC" ] && [ "$(stat -c %a "$LIC")" = 600 ] || { echo "REFUSED: licence file missing or not mode 600 at $LIC (step B)"; exit 2; }
# the formal and batch jobs with their dependencies, in registration order, from pbs/HPC_PLAN.txt (= b4_batch4.py hpc-plan, written by hpc/make_pbs.sh):
# v2 F1, F2 (after:F1), batch (afterany:F1:F2); V3 HPC (RUN_PLAN_HPC_V3.md 4) F1, F2 (after:F1), F3 (afterany:F1), F4 (afterany:F2), batch (afterany:F3:F4)
[ -f pbs/HPC_PLAN.txt ] || { echo "REFUSED: pbs/HPC_PLAN.txt missing (hpc/make_pbs.sh)"; exit 2; }
ST=$(grep '^STATUS|' pbs/HPC_PLAN.txt | cut -d'|' -f2); [ -z "$ST" ] || [ "$ST" = REGISTERED ] || { echo "REFUSED: the limits of the package are $ST (RUN_PLAN_HPC_V3.md section 2) - nothing is submitted before the reviewer and the user registered them"; exit 2; }
ORDER=(); while IFS='|' read -r _ key name _ _ _ _ mode _ depends _; do case "$mode" in formal|batch) ORDER+=("$key|$name|$depends");; esac; done < <(grep '^JOB|' pbs/HPC_PLAN.txt)
[ ${#ORDER[@]} -ge 3 ] || { echo "REFUSED: pbs/HPC_PLAN.txt lists ${#ORDER[@]} formal / batch jobs"; exit 2; }
for x in "${ORDER[@]}"; do IFS='|' read -r key name dep <<< "$x"; [ -f "pbs/$name.pbs" ] || { echo "REFUSED: pbs/$name.pbs missing (hpc/make_pbs.sh)"; exit 2; }; done
if [ -d runs/batch4 ]; then
  [ $RESUME = 1 ] || { echo "REFUSED: runs/batch4 exists - a formal RUN_DIR is used once; --resume only to continue after an interruption (RUN_PLAN_HPC 6)"; exit 2; }
  { [ -f runs/batch4/STOP ] || [ -f runs/batch4/STOP_SAFE ]; } && { echo "REFUSED: runs/batch4 holds STOP / STOP_SAFE - the user resolves it first (a resource restart is a NEW RUN_DIR with authorisation)"; exit 2; }
  for d in runs/batch4/F*; do [ -d "$d" ] || continue; c=$(cat "$d/.cond" 2>/dev/null); case "$c" in build_only|split_built|stopped_before_solve) echo "REFUSED: $d holds a dry-run leftover"; exit 2;; esac; done
fi
command -v qsub > /dev/null 2>&1 || { echo "REFUSED: qsub not found (login node?)"; exit 2; }
declare -A JID; LINE="SUBMITTED:utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"; QUEUED=""
for x in "${ORDER[@]}"; do
  IFS='|' read -r key name dep <<< "$x"; W=()
  if [ -n "$dep" ]; then t=${dep%%:*}; ids=""; for k in $(echo "${dep#*:}" | tr ':' ' '); do [ -n "${JID[$k]:-}" ] || { echo "REFUSED: $key depends on $k, not submitted before it (pbs/HPC_PLAN.txt order)"; exit 2; }; ids="$ids:${JID[$k]}"; done; W=(-W "depend=$t$ids"); fi
  id=$(qsub "${W[@]}" "pbs/$name.pbs") || { if [ -n "$QUEUED" ]; then echo "qsub $key failed - already queued:$QUEUED (qdel them if you do not want them alone)"; else echo "qsub $key failed - nothing submitted; fix the qsub error and run this command again"; fi; exit 1; }
  JID[$key]=$id; QUEUED="$QUEUED $key=$id"; LINE="$LINE:$key=$id"
  [ -d runs/batch4 ] || mkdir -p runs/batch4   # created only after the first job is queued (review F-11: a failed first qsub must not block the retry)
  echo "$key job id: $id${dep:+   (depend=$dep)}"
done
echo "$LINE:resume=$RESUME" | tee -a runs/batch4/SUBMITTED.txt
echo "F2 starts after F1 started; its Gurobi process waits for F1's Gurobi start + 330 s. F3 / F4 (when in the plan) start after F1 / F2 ended; every Gurobi start takes the start lock (>= 330 s after any other start or end, < 2 other sessions). The batch job runs after all runs ended."
echo "monitor: bash hpc/hpr_status.sh"
