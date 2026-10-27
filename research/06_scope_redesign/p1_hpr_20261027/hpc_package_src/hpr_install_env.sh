#!/bin/bash
# HPR install job body (RUN_PLAN_HPC 9, step C; serial queue, 1 core): the environment is installed ON A COMPUTE NODE (the login node kills interactive
# processes after 30 min of CPU time): (1) Miniforge in $HOME/miniforge3 - the installer is downloaded by this job (the compute nodes reach the
# internet: HPC_FACTS, job 1028392), or taken from MINIFORGE_SH / <package>/Miniforge3-Linux-x86_64.sh when the user downloaded it on the login node
# (fallback when the compute node cannot reach GitHub); (2) the third-batch locked environment (env/install_env.sh: 538 exact conda builds + 2 PyPI
# packages; package cache and temporary files on scratch, home quota 20 GB); (3) env/env_check.py (key packages identical, else exit 1); (4) the
# code archive unpacked to <package>/repo by the B4P preflight (sha section) + the preflight sections guards, sha, networks, env, profile, code,
# tools (no licence section). Writes <package>/INSTALL_STATUS.txt. Fallback when conda channels are unreachable from the compute node: run on the
# login node ONLY the downloads (conda create --download-only is not available for explicit lists; use the mirrors CONDA_MIRROR_CONDA_FORGE /
# _BIOCONDA if NUS offers one, or ask the admins) - see HPC_OPERATOR_GUIDE.md step C.
set -u
PKG=${PBS_O_WORKDIR:?run under PBS (qsub) - or set PBS_O_WORKDIR}; cd "$PKG" || exit 2
JOBID=${PBS_JOBID:-local}; S="$PKG/INSTALL_STATUS.txt"; T0=$(date +%s)
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }; log() { echo "$*" | tee -a "$S"; }
USER_NAME=${USER:-$(id -un)}; SCRATCH=${HPR_SCRATCH:-$PKG}
MF=${MINIFORGE_DIR:-$HOME/miniforge3}; ENVP=${ENV_PREFIX:-$MF/envs/pypsa-earth}
export CONDA_PKGS_DIRS="$SCRATCH/conda_pkgs_cache" TMPDIR="$SCRATCH/tmp" PIP_CACHE_DIR="$SCRATCH/tmp/pip_cache"; mkdir -p "$CONDA_PKGS_DIRS" "$TMPDIR" "$PIP_CACHE_DIR"
log "INSTALL_START:jobid=$JOBID:node=$(hostname):home=$HOME:scratch=$SCRATCH:miniforge=$MF:env=$ENVP:utc=$(now)"
if [ ! -x "$MF/bin/conda" ]; then
  SH=${MINIFORGE_SH:-$PKG/Miniforge3-Linux-x86_64.sh}
  if [ ! -f "$SH" ]; then
    SH="$TMPDIR/Miniforge3-Linux-x86_64.sh"
    log "MINIFORGE_DOWNLOAD:start:$(now)"
    curl -sSL --max-time 900 -o "$SH" https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh || { log "MINIFORGE_DOWNLOAD_FAILED - download the installer on the login node to $PKG/Miniforge3-Linux-x86_64.sh and resubmit"; exit 1; }
  fi
  log "MINIFORGE_INSTALL:$(now):installer=$SH:bytes=$(stat -c %s "$SH")"
  bash "$SH" -b -p "$MF" > "$PKG/miniforge_install_${JOBID}.log" 2>&1 || { log "MINIFORGE_INSTALL_FAILED (see miniforge_install_${JOBID}.log)"; exit 1; }
  "$MF/bin/conda" config --set auto_activate_base false > /dev/null 2>&1 || true
else log "MINIFORGE:present:$MF"; fi
if [ -e "$ENVP" ]; then
  log "ENV:present:$ENVP (install_env.sh never overwrites; env_check below decides)"
else
  log "ENV_INSTALL:start:$(now)"
  CONDA="$MF/bin/conda" bash env/install_env.sh "$ENVP" > "$PKG/install_env_${JOBID}.log" 2>&1; rc=$?
  log "ENV_INSTALL:exit=$rc:$(( $(date +%s) - T0 ))s:$(grep -E 'CONDA_DONE|PIP_DONE|INSTALL_END|FAILED|MIRROR' "$PKG/install_env_${JOBID}.log" | tr '\n' ';' | cut -c1-400)"
  [ $rc = 0 ] || { log "ENV_INSTALL_FAILED (see install_env_${JOBID}.log)"; exit 1; }
fi
PY="$ENVP/bin/python"
"$PY" env/env_check.py env/ENV_LOCK.txt --out "$PKG/ENV_CHECK.json" > "$PKG/env_check_${JOBID}.txt" 2>&1; rc=$?
log "ENV_CHECK:key_all_equal=$([ $rc = 0 ] && echo true || echo false):$(head -c 300 "$PKG/env_check_${JOBID}.txt")"
[ $rc = 0 ] || { log "ENV_CHECK_FAILED - do not run the batch"; exit 1; }
PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools PY="$PY" bash preflight.sh > "$PKG/preflight_install_${JOBID}.txt" 2>&1; rc=$?
log "PREFLIGHT:exit=$rc:$(tail -1 "$PKG/preflight_install_${JOBID}.txt")"
log "REPO:$(cat repo/.package_commit 2>/dev/null || echo missing):package_commit=$(cat COMMIT)"
log "SIZES:home=$(du -sh "$HOME" 2>/dev/null | cut -f1) (quota 20 GB):env=$(du -sh "$ENVP" 2>/dev/null | cut -f1):scratch=$(du -sh "$SCRATCH" 2>/dev/null | cut -f1) (quota 500 GB, 60-day purge)"
log "INSTALL_END:exit=$rc:seconds=$(( $(date +%s) - T0 )):utc=$(now)"
exit $rc
