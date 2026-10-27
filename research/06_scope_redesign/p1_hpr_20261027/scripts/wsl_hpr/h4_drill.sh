#!/bin/bash
# HPR H4: the local end-to-end drill = the generated smoke job script pbs/hpr_smoke56.pbs executed as bash with simulated PBS_* variables on a copy of the
# package v9 sources (package folder /home/jin/hpr_drill/pkg; runs under the main checkout results_project/hpr/h4_smoke56). Exactly the formal code path:
# hpr_job.sh -> run_batch4.sh --only F1 (process 1 build -> process 2 b4_split_solve.py = Gurobi -> process 3 assign -> per-run post-processing) ->
# --only F2 (WAIT_START_OF=F1; >= 330 s after F1's Gurobi start, here after F1 ended) -> POST_ONLY=1 batch body (reference, regrade, B6, Owen, summary,
# packs). Networks = the v2 2920x3h networks of results_project/dfx_v3/builds_v2 truncated to 56 snapshots (TRUNCATE=56 set by the job body), profile
# formal_barrier_1e6_t16, TimeLimit 3,000 s, wall cap 3,600 s. TWO local Gurobi calls (the instruction's authorisation H4: <= 2, <= 60 min each, >= 5 min
# apart, no retry). The licence is referenced only through GRB_LICENSE_FILE (never read / copied). Afterwards h4_compare.py checks the results against the
# DFX F5.5 smoke bitwise (objective, iterations, X / Pi / RC arrays, exports).
set -u
WT=/home/jin/wt_hpr_20261027; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
SRC=$WT/research/06_scope_redesign/p1_hpr_20261027/hpc_package_src; PKG4=$WT/research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4; PKG3=$WT/research/06_scope_redesign/p1_m10p_20261022/cloud_package
B=$MAIN/results_project/dfx_v3/builds_v2; DRILL=/home/jin/hpr_drill; PKG=$DRILL/pkg; RUNS=$MAIN/results_project/hpr/h4; ST=$RUNS/H4_DRILL_STATUS.txt
export PYTHONHASHSEED=0
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[g]urobi_cl|[b]4_split_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
mkdir -p "$RUNS"
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" | tee -a "$ST"; }
[ "$(busy)" = 0 ] || { log SOLVER_BUSY "$(busy) processes - not started"; exit 4; }
[ "$(ps -eo args= | grep -c '[p]ytest')" = 0 ] || { log PYTEST_RUNNING "stand-in tests must not run during a real solve - not started"; exit 4; }
[ -f /home/jin/gurobi.lic ] || { log NO_LICENCE_FILE; exit 3; }   # existence only
cd "$WT" || exit 1
[ -z "$(git status --porcelain --untracked-files=no)" ] || { log DIRTY_TREE "commit first (the drill must run at the package commit)"; exit 2; }
COMMIT=$(git rev-parse HEAD)
# the package-like folder (as the v9 package: runner, preflight, pack, env, hpc/, pbs/, networks = the registered files, repo -> the worktree code)
rm -rf "$PKG"; mkdir -p "$PKG/networks" "$PKG/env" "$PKG/hpc"
for sc in integrated disconnected; do cp "$B/$sc/${sc}_2920_3h_unsolved.nc" "$B/$sc/${sc}_BUILD_RECEIPT.json" "$PKG/networks/"; cp "$B/$sc/costs_active_research.csv" "$PKG/networks/${sc}_costs_active_research.csv"; done
cp "$PKG4/run_batch4.sh" "$PKG4/preflight.sh" "$PKG3/pack_results.sh" "$PKG/"; cp "$PKG3"/env/* "$PKG/env/"; cp "$SRC"/*.sh "$SRC"/*.py "$PKG/hpc/"
cp "$WT/research/06_scope_redesign/p1_hpr_20261027/REFERENCE_VALUES.json" "$PKG/"
echo "$COMMIT" > "$PKG/COMMIT"
# the code archive exactly as the package builder makes it (git archive of HEAD without research/); the in-job preflight (sha section) unpacks it to ./repo
mapfile -t FILES < <(git ls-tree -r --name-only "$COMMIT" | grep -v '^research/')
git --literal-pathspecs archive --format=tar.gz -o "$PKG/code_${COMMIT:0:8}.tar.gz" "$COMMIT" -- "${FILES[@]}" || { log GIT_ARCHIVE_FAILED; exit 2; }
( cd "$PKG" && find . -type f ! -name SHA256SUMS -printf '%P\n' | LC_ALL=C sort | xargs sha256sum > SHA256SUMS )
( cd "$PKG" && REPO=$WT PY=$PY bash hpc/make_pbs.sh pbs > pbs/MAKE_PBS.log 2>&1 ) || { log MAKE_PBS_FAILED; exit 2; }
# the user authorisation text of the drill (instruction H4; no host, no account, no licence)
echo "HPR H4 local drill (instruction f14cb018, 2026-10-27): two 56-snapshot smoke runs of the v2 2920x3h networks through the PBS job bodies as bash, TimeLimit 3000 s, wall cap 3600 s, no retry" > "$PKG/HPR_AUTH.txt"; chmod 600 "$PKG/HPR_AUTH.txt"
log START "commit=$COMMIT:pkg=$PKG:runs=$RUNS:networks=builds_v2:truncate=56"
# the smoke job script as bash with simulated PBS variables (PBS_O_WORKDIR = the package folder; PBS_JOBID local...; NCPUS as the job request)
export PBS_O_WORKDIR=$PKG PBS_JOBID=local.h4drill NCPUS=17 PBS_JOBNAME=hpr_smoke56 PBS_QUEUE=parallel HPR_LOCAL_DRILL=1 HPR_RUN_ROOT=$RUNS GRB_LICENSE_FILE=/home/jin/gurobi.lic PY=$PY
t0=$(date +%s)
bash "$PKG/pbs/hpr_smoke56.pbs" > "$RUNS/smoke56_job.out" 2>&1; rc=$?
log JOB_EXIT "exit=$rc:seconds=$(( $(date +%s) - t0 ))"
tail -5 "$RUNS/runs/smoke56/PBS_JOBS.txt" 2>/dev/null | cut -c1-240 | tee -a "$ST"
cat "$RUNS/runs/smoke56/SMOKE_STATUS.txt" 2>/dev/null | tee -a "$ST"
log DONE "exit=$rc"
