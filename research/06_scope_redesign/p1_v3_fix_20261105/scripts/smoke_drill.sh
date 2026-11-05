#!/bin/bash
# V3.1 section 5.2: local 56x3h regression through the HPC smoke job body of the v3.1 DRILL package (runner run_batch4.sh, TRUNCATE=56, split mode, profile
# formal_barrier_1e6_t16, TimeLimit 3,000 s / wall cap 3,600 s as the HPC smoke): F1, F2 (2 Gurobi calls, serial, the runner keeps >= 330 s between the sessions),
# then the batch-level body (no licence). Local drill switches only (HPR_LOCAL_DRILL=1: no token-server curl, no resources section). No retry, no parameter change.
#   bash smoke_drill.sh <drill package dir>
set -u
PKG=${1:?drill package dir}; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; LIC=/home/jin/gurobi.lic
EV=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_fix_20261105/evidence; CALLS=$EV/GUROBI_CALLS.csv; ST=$EV/FIX_STATUS.txt; MAXCALLS=6
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }; log() { echo "$*" >> "$ST"; echo "$*"; }
busy() { ps -eo args= | grep -E '[b]4_split_solve\.py|[s]2_solve\.py|[d]iag_build\.py|[g]urobi_cl|[p]ytest' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
token_ok() { timeout 15 bash -c 'exec 3<>/dev/tcp/token.gurobi.com/443' 2>/dev/null; }
calls_used() { tail -n +2 "$CALLS" | grep -c .; }
[ -f "$PKG/DRILL_ONLY_NOT_FOR_UPLOAD.txt" ] || { log "DRILL_REFUSED: $PKG is not a drill package"; exit 2; }
[ "$(cat "$PKG/COMMIT")" = "$(git -C /home/jin/wt_v3_fix rev-parse HEAD)" ] || { log "DRILL_REFUSED: drill package commit differs from the fix worktree head"; exit 2; }
[ -f "$LIC" ] && [ "$(stat -c %a "$LIC")" = 600 ] || { log "DRILL_REFUSED: licence file missing or not mode 600 (attributes only)"; exit 2; }
[ ! -e "$PKG/runs/smoke56_v31" ] || { log "DRILL_REFUSED: $PKG/runs/smoke56_v31 exists - never repeated"; exit 2; }
cd "$PKG" || exit 2
eval "$(grep '^export JOB_' pbs/hpr3_smoke56.pbs)"   # the job script's own JOB_* values (ncpus 17, mem 32 GB, walltime 04:00:00, mode smoke56)
export PBS_O_WORKDIR="$PKG" HPR_LOCAL_DRILL=1 GRB_LICENSE_FILE="$LIC" PY="$PY"
export HPR_AUTH="V3.1 local regression (decision 195, V3_FIX_INSTRUCTION.md 5.2; start confirmed by the user 2026-11-05: AnyConnect disconnected, no other Gurobi process): 56-snapshot F1 / F2 through the v3.1 smoke job body, no retry"
unset BATCH_DEF PBS_JOBID
log "DRILL_START:package=$PKG:commit=$(cat COMMIT):job=$JOB_NAME:ncpus=$JOB_NCPUS:mem_gb=$JOB_MEM_GB:$(now)"
for rid in F1 F2 batch; do
  if [ "$rid" != batch ]; then
    used=$(calls_used); [ "$used" -lt "$MAXCALLS" ] || { log "DRILL_STOP:$rid:Gurobi budget $used/$MAXCALLS used"; exit 3; }
    [ "$(busy)" = 0 ] || { log "DRILL_STOP:$rid:$(busy) solver / pytest processes running"; exit 3; }
    token_ok || { log "DRILL_STOP:$rid:no TCP to the token server (AnyConnect?) - no Gurobi call made"; exit 3; }
    k=$((used + 1)); s0=$(now); log "GUROBI_CALL_$k:smoke56_v31_$rid:job body (run_batch4.sh --only $rid, TRUNCATE=56, split):start:$s0"
  fi
  t0=$(date +%s)
  JOB_RID=$rid bash hpc/hpr_job.sh > "$EV/drill_job_$rid.out" 2>&1; rc=$?
  log "DRILL_JOB:$rid:exit=$rc:$(( $(date +%s) - t0 ))s:$(tail -1 runs/smoke56_v31/STATUS.txt 2>/dev/null | cut -c1-200):$(now)"
  if [ "$rid" != batch ]; then
    R=runs/smoke56_v31/$rid
    st=$("$PY" -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('gurobi_status_name'), d.get('bar_iter_count'), d.get('runtime_s'), d.get('max_mem_used_gb'))" "$R/split/SPLIT_SOLVE.json" 2>/dev/null || echo "? ? ? ?")
    read -r gs it rt mm <<< "$st"
    echo "$k,smoke56_v31_$rid,job_body,$s0,$(now),$rc,$gs,,$rt,$mm,,iterations=$it TRUNCATE=56 split formal_barrier_1e6_t16 (HPC smoke job body, local drill)" >> "$CALLS"
    [ $rc = 0 ] || { log "DRILL_STOP:$rid:job body exit $rc - the next run is not started (no retry)"; exit 3; }
  fi
done
log "DRILL_DONE:$(now)"; cat runs/smoke56_v31/SMOKE_STATUS.txt
