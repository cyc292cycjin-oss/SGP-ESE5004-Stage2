#!/bin/bash
# DFX phase 2 (PROPOSED, offline draft; NOT stand-in tested - README_HPC section 4): PBS job body of dfx_f1_integrated.pbs / dfx_f2_disconnected.pbs -
# ONE run (JOB_RID = F1 | F2) of the fourth batch in its own PBS job: the B4P split-process solve (process 1 s2_solve.py --split-stage build, process 2
# b4_split_solve.py = the only Gurobi process, process 3 s2_solve.py --split-stage assign; RUN_PLAN_B4 3.1) and the per-run post-processing (violations
# -> C1 with the default reference -> M12 -> Owen dual form -> GATES_V6 -> stop-class). The batch-level steps (C1 reference from F1 / F2, regrade, B6,
# summary, packs) are hpc_batch_post.sh after both jobs. One solve per run, never repeated (an ended run is skipped; a started-not-ended run is a
# safe stop for the user). The wall-clock cap of process 2 is enforced with timeout (TERM, KILL 60 s later).
# Reads: JOB_RID, JOB_NCPUS, JOB_MEM_GB, JOB_TIME_LIMIT_S (generated .pbs), DFX_AUTH (qsub -v), PBS_O_WORKDIR = package folder on scratch.
# TimeLimit: the registered value of the fourth batch is 259,200 s (RUN_PLAN_B4 3.1); JOB_TIME_LIMIT_S is used ONLY after the user has registered it
# (README_HPC section 5) - the receipt records whatever value was used, so a formal run with an unregistered value is visible in the results.
set -u
: "${PBS_O_WORKDIR:?run under PBS (qsub)}"; : "${DFX_AUTH:?qsub -v DFX_AUTH=\"<user authorisation text>\" is required}"; : "${JOB_RID:?F1 or F2}"
PKG="$PBS_O_WORKDIR"; cd "$PKG" || exit 2
USER_NAME=${USER:-$(id -un)}; SCRATCH=${HPCTMP:-/hpctmp/$USER_NAME}/dfx_hpc
REPO=${REPO:-$HOME/dfx_hpc/repo}; PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}; NETS="$PKG/networks"
OUT=${RUN_DIR:-$SCRATCH/runs/batch4_two}; export TMPDIR="$SCRATCH/tmp"; mkdir -p "$OUT" "$TMPDIR"; ST="$OUT/STATUS.txt"
export GRB_LICENSE_FILE=${GRB_LICENSE_FILE:-$HOME/.gurobi/gurobi.lic}; export PYTHONHASHSEED=0
TL=${JOB_TIME_LIMIT_S:-259200}; WALL=$(( TL + 7200 )); BUILD_TIMEOUT_S=3600; ASSIGN_TIMEOUT_S=32400; POST_TIMEOUT_S=10800
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }; log() { echo "$*" >> "$ST"; }
[ -f "$GRB_LICENSE_FILE" ] && [ "$(stat -c %a "$GRB_LICENSE_FILE")" = 600 ] || { log "STOP_SAFE:LICENCE_FILE_MISSING_OR_MODE_NOT_600:$JOB_RID:$(now)"; exit 2; }
rid=$JOB_RID; d="$OUT/$rid"; mkdir -p "$d"
IFS='|' read -r _ sc base _ prof costs < <(cd "$REPO" && "$PY" scripts_project/b4_batch4.py runtable | grep "^$rid|")
[ -n "${sc:-}" ] || { log "STOP_SAFE:RUN_TABLE:$rid not in b4_batch4.py:$(now)"; exit 2; }
net="$NETS/${base}_unsolved.nc"; costs_csv="$NETS/${costs}_costs_active_research.csv"
log "JOB_START:$rid:${PBS_JOBID:-?}:host=$(hostname):ncpus=${JOB_NCPUS:-?}:mem_gb=${JOB_MEM_GB:-?}:time_limit=$TL:wall=$WALL:$(now)"
[ -f "$d/.ended" ] && { log "SKIP_ENDED_$rid:$(cat "$d/.cond" 2>/dev/null) (never re-solved):$(now)"; exit 0; }
[ -f "$d/.started" ] && { log "STOP_SAFE:INTERRUPTED_$rid:started $(cat "$d/.started") but never ended - not repeated; user decision (RUN_PLAN_B4 3.8):$(now)"; exit 3; }
# phase 0 of this run: the base network against the build receipt and the fourth-batch registered value (b4_batch4.py base-check: both networks)
( cd "$REPO" && env -u GRB_LICENSE_FILE "$PY" scripts_project/b4_batch4.py base-check --nets "$NETS" --out "$OUT/BASE_CHECK_$rid.json" ) > "$d/base_check.log" 2>&1 || { log "STOP_SAFE:BASE_NETWORK_SHA256:$rid:$(tail -1 "$d/base_check.log"):$(now)"; exit 3; }
cmd=("$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario "$sc" --output "$d" --label BATCH4_2920X3H --authorization "$DFX_AUTH; run $rid" \
     --solver gurobi --solver-profile "$prof" --scaling on --time-limit "$TL" --costs-table "$costs_csv")
now > "$d/.started"
# process 1: build + LP arrays + problem file (no licence)
( cd "$REPO" && exec env -u GRB_LICENSE_FILE timeout -k 60 "$BUILD_TIMEOUT_S" /usr/bin/time -v "${cmd[@]}" --split-stage build > "$d/p1.log" 2> "$d/p1.err" ); ex=$?
log "BUILD_$rid:exit=$ex:peak=$(grep -h 'Maximum resident' "$d/p1.err" 2>/dev/null | awk '{printf "%.2fGiB", $NF/1048576}'):$(now)"
[ $ex = 0 ] && [ -f "$d/split/SPLIT_BUILD.json" ] || { log "STOP_SAFE:BUILD_FAILED_$rid:exit=$ex (no Gurobi call made):$(now)"; now > "$d/.ended"; echo build_failed > "$d/.cond"; exit 3; }
# process 2: the only Gurobi process; wall-clock cap by timeout; monitor every 60 s (RSS of this process group, cgroup memory)
t0=$(date +%s)
( cd "$REPO" && exec timeout -k 60 "$WALL" /usr/bin/time -v env GRB_LICENSE_FILE="$GRB_LICENSE_FILE" "$PY" scripts_project/b4_split_solve.py --run-dir "$d" --remove-lp > "$d/p2.log" 2> "$d/p2.err" ) &
pid=$!; f="$OUT/MONITOR_$rid.csv"; echo "utc,elapsed_s,rss_gib,cgroup_mem_gib,gurobi_last_line" > "$f"
while kill -0 $pid 2>/dev/null; do
  rss=$(ps -o rss= --ppid $pid 2>/dev/null | awk '{s+=$1} END {printf "%.2f", s/1048576}'); cg=$(cat /sys/fs/cgroup/memory.current 2>/dev/null || cat /sys/fs/cgroup/memory/memory.usage_in_bytes 2>/dev/null || echo "")
  echo "$(now),$(( $(date +%s) - t0 )),$rss,$([ -n "$cg" ] && awk -v b="$cg" 'BEGIN {printf "%.2f", b/1073741824}'),$(tail -n 1 "$d/gurobi.linopy.log" 2>/dev/null | grep -viE 'licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic' | tr ',' ';' | cut -c1-120)" >> "$f"
  sleep 60
done
wait $pid; ex=$?; date +%s > "$d/.solve_end"
S="$d/split/SPLIT_SOLVE.json"
log "GUROBI_$rid:exit=$ex:$(( $(date +%s) - t0 ))s:status=$("$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('gurobi_status_name'), r.get('termination_condition'), r.get('bar_iter_count'), r.get('objective'), r.get('max_mem_used_gb'))" "$S" 2>/dev/null):peak=$(grep -h 'Maximum resident' "$d/p2.err" 2>/dev/null | awk '{printf "%.2fGiB", $NF/1048576}'):$(now)"
# process 3: map back + post-solve exports (no licence) - only when process 2 wrote a termination condition
cond=none
if [ -n "$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition') or '')" "$S" 2>/dev/null)" ]; then
  ( cd "$REPO" && exec env -u GRB_LICENSE_FILE timeout -k 60 "$ASSIGN_TIMEOUT_S" /usr/bin/time -v "${cmd[@]}" --split-stage assign > "$d/p3.log" 2> "$d/p3.err" ); ex3=$?
  log "ASSIGN_$rid:exit=$ex3:peak=$(grep -h 'Maximum resident' "$d/p3.err" 2>/dev/null | awk '{printf "%.2fGiB", $NF/1048576}'):$(now)"
  cond=$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition') or 'none')" "$d/SOLVE_RECEIPT.json" 2>/dev/null || echo none)
else
  cond=killed_or_no_result
fi
echo "$cond" > "$d/.cond"; echo "$ex" > "$d/.exit"; now > "$d/.ended"; log "RUN_$rid:$cond:exit=$ex:$(now)"
# per-run post-processing (no licence); the batch reference / regrade come with hpc_batch_post.sh
P() { ( cd "$REPO" && exec env -u GRB_LICENSE_FILE timeout -k 60 "$POST_TIMEOUT_S" /usr/bin/time -v "$PY" "$@" ); }
[ -f "$d/solution/X.npy" ] && { P scripts_project/l23_violation_analysis.py --repo . --solve-dir "$d" --network "$net" --scenario "$sc" --label BATCH4_2920X3H --out "$d/VIOLATIONS.json" > "$d/c1_violations.log" 2> "$d/c1_violations.err"; log "VIOLATIONS_$rid:exit=$?"; }
P scripts_project/s4o_c1_precision.py run --repo . --solve-dir "$d" --network "$net" --scenario "$sc" --label BATCH4_2920X3H --violations "$d/VIOLATIONS.json" > "$d/c1_precision.log" 2> "$d/c1_precision.err"; log "C1_$rid:exit=$?:provisional"
[ -f "$d/SOLVE_RECEIPT.json" ] && { P scripts_project/m12_allocation.py run --repo . --solve-dir "$d" --scenario "$sc" --label "BATCH4_$rid" --out "$d" --register > "$d/m12.log" 2> "$d/m12.err"; log "M12_$rid:exit=$?"; }
[ -f "$d/solution/X.npy" ] && [ -f "$d/ALLOCATION.json" ] && { P scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario "$sc" --solve-dir "$d" --allocation "$d/ALLOCATION.json" --tag "BATCH4_$rid" --out "$d/m12_owen" --register-dir "$d" > "$d/m12_owen.log" 2> "$d/m12_owen.err"; log "M12_OWEN_$rid:exit=$?"; }
lab=$(P scripts_project/v5/gates_v6.py accept --solve-dir "$d" --build-receipt "$NETS/${sc}_BUILD_RECEIPT.json" --repo . 2> "$d/v6.err" | tail -1); echo "$lab" > "$d/.label"; log "V6_$rid:$lab:provisional"
read -r cls act < <(P scripts_project/b4_batch4.py stop-class --dir "$d" 2> "$d/stop_class.err" | tail -1); log "CLASS_$rid:${cls:-unreadable}:${act:-stop}:$(now)"
[ "${act:-stop}" = none ] || [ "$lab" = ACCEPTED_LAYER1 ] || [ "$lab" = ACCEPTED_LAYER2 ] || { echo "$rid" >> "$OUT/STOP"; log "STOP_NOT_ACCEPTED:$rid:${cls:-unreadable}:$(now) - user decision"; }
log "JOB_END:$rid:$(now)"
[ -f "$OUT/STOP" ] && exit 3 || exit 0
