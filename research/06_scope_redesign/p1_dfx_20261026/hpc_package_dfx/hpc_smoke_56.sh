#!/bin/bash
# DFX phase 2 (PROPOSED, offline draft): PBS job body of dfx_smoke_56.pbs - the first validation of the environment on a compute node after the
# account is ready: (1) token.gurobi.com reachability from the compute node (HTTP status only), (2) ONE split-process solve of the integrated 2920x3h
# v2 network truncated to 56 snapshots (profile formal_barrier_1e6_t16, TimeLimit 3,000 s; process 1 build -> process 2 gurobipy -> process 3 assign),
# (3) the post-processing chain (violations -> C1 -> M12 -> Owen dual form -> GATES_V6 -> stop-class). One Gurobi call; no retry.
# Reads: DFX_AUTH (qsub -v), PBS_O_WORKDIR = the package folder on scratch. Writes SMOKE_STATUS.txt under $HPCTMP/dfx_hpc/runs/smoke_56.
set -u
: "${PBS_O_WORKDIR:?run under PBS (qsub)}"; : "${DFX_AUTH:?qsub -v DFX_AUTH=\"<user authorisation text>\" is required}"
PKG="$PBS_O_WORKDIR"; cd "$PKG" || exit 2
USER_NAME=${USER:-$(id -un)}; SCRATCH=${HPCTMP:-/hpctmp/$USER_NAME}/dfx_hpc
REPO=${REPO:-$HOME/dfx_hpc/repo}; PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}; NETS="$PKG/networks"
RUN=${RUN_DIR:-$SCRATCH/runs/smoke_56}; export TMPDIR="$SCRATCH/tmp"; mkdir -p "$RUN" "$TMPDIR"; ST="$RUN/SMOKE_STATUS.txt"
export GRB_LICENSE_FILE=${GRB_LICENSE_FILE:-$HOME/.gurobi/gurobi.lic}; export PYTHONHASHSEED=0
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> "$ST"; }
[ -f "$GRB_LICENSE_FILE" ] && [ "$(stat -c %a "$GRB_LICENSE_FILE")" = 600 ] || { log LICENCE_FILE_MISSING_OR_MODE_NOT_600; exit 2; }
log START "job=${PBS_JOBID:-?}:host=$(hostname):ncpus=${JOB_NCPUS:-?}:mem_gb=${JOB_MEM_GB:-?}:commit=$(cat "$PKG/COMMIT" 2>/dev/null)"
# 1. WLS token server reachability from the compute node (status code only; nothing else of the request is logged)
code=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 30 https://token.gurobi.com 2>/dev/null || echo "curl_failed")
log WLS_TOKEN_HTTP "$code (302 or 200 expected; HPC_FACTS: job 1028392 saw 302)"
case "$code" in 200|301|302) ;; *) log STOP "token.gurobi.com not reachable from this compute node - no solve attempted"; exit 3;; esac
# 2. one split-process solve, 56 snapshots, integrated
sc=integrated; net="$NETS/${sc}_2920_3h_unsolved.nc"; d="$RUN/$sc"; mkdir -p "$d"
[ -f "$d/SOLVE_RECEIPT.json" ] && { log SKIP_EXISTING "no re-solve"; exit 0; }
cmd=("$PY" scripts_project/s2_solve.py --repo . --network "$net" --scenario $sc --output "$d" --label SMOKE_TEST_ONLY --authorization "$DFX_AUTH; HPC smoke 56" \
     --solver gurobi --solver-profile formal_barrier_1e6_t16 --scaling on --time-limit 3000 --costs-table "$NETS/${sc}_costs_active_research.csv" --truncate 56)
( cd "$REPO" && env -u GRB_LICENSE_FILE timeout -k 60 3600 /usr/bin/time -v "${cmd[@]}" --split-stage build > "$d/p1.log" 2> "$d/p1.err" ); log P1_BUILD "exit=$?:peak=$(grep -h 'Maximum resident' "$d/p1.err" | awk '{printf "%.2fGiB", $NF/1048576}')"
[ -f "$d/split/SPLIT_BUILD.json" ] || { log STOP "process 1 did not write split/SPLIT_BUILD.json"; exit 3; }
( cd "$REPO" && timeout -k 60 3600 /usr/bin/time -v env GRB_LICENSE_FILE="$GRB_LICENSE_FILE" "$PY" scripts_project/b4_split_solve.py --run-dir "$d" --remove-lp > "$d/p2.log" 2> "$d/p2.err" )
log P2_GUROBI "exit=$?:status=$("$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('gurobi_status_name'), r.get('termination_condition'), r.get('bar_iter_count'), r.get('objective'))" "$d/split/SPLIT_SOLVE.json" 2>/dev/null):peak=$(grep -h 'Maximum resident' "$d/p2.err" | awk '{printf "%.2fGiB", $NF/1048576}')"
( cd "$REPO" && env -u GRB_LICENSE_FILE timeout -k 60 7200 /usr/bin/time -v "${cmd[@]}" --split-stage assign > "$d/p3.log" 2> "$d/p3.err" ); log P3_ASSIGN "exit=$?:peak=$(grep -h 'Maximum resident' "$d/p3.err" | awk '{printf "%.2fGiB", $NF/1048576}')"
cond=$("$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print(r.get('termination_condition'), r.get('objective'))" "$d/SOLVE_RECEIPT.json" 2>/dev/null || echo no_receipt); log SOLVE "$cond"
# 3. post-processing chain (no licence)
P() { ( cd "$REPO" && env -u GRB_LICENSE_FILE timeout -k 60 3600 /usr/bin/time -v "$PY" "$@" ); }
[ -f "$d/solution/X.npy" ] && { P scripts_project/l23_violation_analysis.py --repo . --solve-dir "$d" --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --out "$d/VIOLATIONS.json" --truncate 56 > "$d/c1_violations.log" 2> "$d/c1_violations.err"; log VIOLATIONS "exit=$?"; }
P scripts_project/s4o_c1_precision.py run --repo . --solve-dir "$d" --network "$net" --scenario $sc --label SMOKE_TEST_ONLY --violations "$d/VIOLATIONS.json" --truncate 56 > "$d/c1_precision.log" 2> "$d/c1_precision.err"; log C1 "exit=$?"
P scripts_project/m12_allocation.py run --repo . --solve-dir "$d" --scenario $sc --label SMOKE_$sc --out "$d" --register > "$d/m12.log" 2> "$d/m12.err"; log M12 "exit=$?"
P scripts_project/m12_rhs_audit.py audit --repo . --network "$net" --scenario $sc --solve-dir "$d" --allocation "$d/ALLOCATION.json" --tag SMOKE_$sc --out "$d/m12_owen" --register-dir "$d" --truncate 56 > "$d/m12_owen.log" 2> "$d/m12_owen.err"; log OWEN "exit=$?"
lab=$(P scripts_project/v5/gates_v6.py accept --solve-dir "$d" --build-receipt "$NETS/${sc}_BUILD_RECEIPT.json" --repo . --out "$d/V6_ACCEPTANCE.json" 2> "$d/v6.err" | tail -1); log V6 "$lab"
P scripts_project/b4_batch4.py stop-class --dir "$d" > "$d/stop_class.log" 2>&1; log STOPCLASS "$(tail -1 "$d/stop_class.log")"
log DONE "optimal_expected=$([ "${cond%% *}" = optimal ] && echo yes || echo NO)"
