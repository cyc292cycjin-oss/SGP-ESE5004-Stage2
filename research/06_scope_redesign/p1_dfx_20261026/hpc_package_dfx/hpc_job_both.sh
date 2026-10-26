#!/bin/bash
# DFX phase 2 (PROPOSED, offline draft): PBS job body of dfx_f12_both.pbs - the fourth-batch runner run_batch4.sh AS IS (F1 integrated, F2 disconnected,
# 2920x3h v2 networks, SOLVE_MODE=split, P1 probe, memory stop, projection stop, graded stop rule; RUN_PLAN_B4 section 3) inside one PBS job.
# Reads: JOB_NCPUS / JOB_MEM_GB (exported by the generated .pbs), DFX_AUTH (qsub -v DFX_AUTH="<user authorisation text>"), PBS_O_WORKDIR = the
# package folder on scratch ($HPCTMP/dfx_hpc/package: networks/, run_batch4.sh, preflight.sh, pack_results.sh, env/, hpc/, repo -> $HOME/dfx_hpc/repo).
# Paths (README_HPC section 2): code + environment in $HOME, networks / runs / logs / results on /hpctmp (60-day purge: download the packs at once).
# PREREQUISITE (README_HPC section 5-6): the fourth-batch registered inputs (scripts_project/b4_batch4.py REGISTERED_SHA / BYTES / BUILD_COMMIT) and
# limits (run_batch4.sh R_TL / R_WALL) must have been re-registered for the v2 networks and the HPC TimeLimit with the user's authorisation before this
# job is submitted - otherwise phase 0 of run_batch4.sh stops safely (BASE_NETWORK_SHA256) by design.
set -u
: "${PBS_O_WORKDIR:?run under PBS (qsub)}"; : "${DFX_AUTH:?qsub -v DFX_AUTH=\"<user authorisation text>\" is required}"
PKG="$PBS_O_WORKDIR"; cd "$PKG" || exit 2
USER_NAME=${USER:-$(id -un)}; SCRATCH=${HPCTMP:-/hpctmp/$USER_NAME}/dfx_hpc
export REPO=${REPO:-$HOME/dfx_hpc/repo}; export PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}; export NETS="$PKG/networks"
export RUN_DIR=${RUN_DIR:-$SCRATCH/runs/batch4}; export TMPDIR="$SCRATCH/tmp"; mkdir -p "$RUN_DIR" "$TMPDIR"
export GRB_LICENSE_FILE=${GRB_LICENSE_FILE:-$HOME/.gurobi/gurobi.lic}
[ -f "$GRB_LICENSE_FILE" ] && [ "$(stat -c %a "$GRB_LICENSE_FILE")" = 600 ] || { echo "LICENCE_FILE_MISSING_OR_MODE_NOT_600:$GRB_LICENSE_FILE (existence and mode checked only)"; exit 2; }
export CORES=${JOB_NCPUS:?} MEM_QUOTA_GIB=${JOB_MEM_GB:?} SOLVE_MODE=split REMOVE_LP=1 PYTHONHASHSEED=0
J="$RUN_DIR/PBS_JOBS.txt"; echo "JOB_START:${PBS_JOBID:-?}:host=$(hostname):ncpus=$CORES:mem_gb=$MEM_QUOTA_GIB:walltime=${JOB_WALLTIME:-?}:utc=$(date -u +%FT%TZ)" >> "$J"
# cgroup memory as PBS set it (information: the runner's monitor uses memory.max when present, else MEM_QUOTA_GIB)
for f in /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory/memory.limit_in_bytes; do [ -r "$f" ] && echo "CGROUP:$f=$(cat "$f")" >> "$J"; done
# preflight inside the job (B4P preflight.sh; the licence section holds one WLS token >= 5 min, the runner waits 330 s before its first solve)
PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools,licence,resources NEED_CORES=17 NEED_MEM_GIB=$(( MEM_QUOTA_GIB * 8 / 10 )) NEED_DISK_GB=45 PREFLIGHT_DISK_PATH="$SCRATCH" \
  bash "$PKG/preflight.sh" > "$RUN_DIR/preflight_${PBS_JOBID:-job}.txt" 2>&1; rc=$?
echo "PREFLIGHT:exit=$rc:$(tail -1 "$RUN_DIR/preflight_${PBS_JOBID:-job}.txt")" >> "$J"
[ $rc = 0 ] || { echo "PREFLIGHT_FAILED - job ends (nothing solved)" >> "$J"; exit 1; }
# the batch (resume-safe: the same qsub again continues in the same RUN_DIR; an ended solve is never repeated)
bash "$PKG/run_batch4.sh" --auth "$DFX_AUTH"; rc=$?
echo "RUNNER:exit=$rc:utc=$(date -u +%FT%TZ):status_tail=$(tail -1 "$RUN_DIR/STATUS.txt" 2>/dev/null | cut -c1-200)" >> "$J"
# results: the packs written by the runner (light / full) + their .sha256 - download within 60 days
ls -l "$RUN_DIR"/results_*.tar.gz "$RUN_DIR"/results_*.tar.gz.sha256 2>/dev/null >> "$J"
exit $rc
