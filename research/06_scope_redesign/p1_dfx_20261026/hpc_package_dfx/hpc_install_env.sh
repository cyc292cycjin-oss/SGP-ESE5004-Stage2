#!/bin/bash
# DFX phase 2 (PROPOSED, offline draft): one-time environment install on the NUS Atlas LOGIN node (atlas8: internet access; CPU time of an interactive
# process is limited to 30 min - the conda create of ~540 packages took ~14 min on AutoDL; if it is killed, re-run: an existing prefix is never
# overwritten, remove the incomplete prefix by hand first).
#   bash hpc/hpc_install_env.sh            from the package folder on scratch ($HPCTMP/dfx_hpc/package)
# Steps: (1) Miniforge in $HOME/miniforge3 (installer downloaded from GitHub unless MINIFORGE_SH=<local installer> is given; the cluster's conda modules
# are 3.6-4.12 and not used), (2) the third-batch locked environment via env/install_env.sh (exact conda builds + 2 PyPI packages; key packages must
# be identical: env/env_check.py), package cache and temporary files on scratch (home quota 20 GB), (3) the code archive unpacked to $HOME/dfx_hpc/repo
# and linked as ./repo (the B4P preflight / runner expect ./repo next to the package files), (4) quota report. The licence is NOT touched: put it
# yourself at $HOME/.gurobi/gurobi.lic with chmod 600 (never into the package, the repo, a log or a job script).
set -eu
PKG="$(cd "$(dirname "$0")/.." && pwd)"; cd "$PKG"
USER_NAME=${USER:-$(id -un)}; SCRATCH=${HPCTMP:-/hpctmp/$USER_NAME}/dfx_hpc; mkdir -p "$SCRATCH/conda_pkgs_cache" "$SCRATCH/tmp"
MF=${MINIFORGE_DIR:-$HOME/miniforge3}; ENVP=${ENV_PREFIX:-$MF/envs/pypsa-earth}
export CONDA_PKGS_DIRS="$SCRATCH/conda_pkgs_cache" TMPDIR="$SCRATCH/tmp" PIP_CACHE_DIR="$SCRATCH/tmp/pip_cache"
echo "INSTALL_START:$(date -u +%FT%TZ):home=$HOME:scratch=$SCRATCH:miniforge=$MF:env=$ENVP"
if [ ! -x "$MF/bin/conda" ]; then
  SH=${MINIFORGE_SH:-$SCRATCH/tmp/Miniforge3-Linux-x86_64.sh}
  if [ ! -f "$SH" ]; then
    echo "downloading the Miniforge installer to $SH (login node has internet access; the compute nodes may not)"
    curl -L --max-time 600 -o "$SH" https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
  fi
  bash "$SH" -b -p "$MF"
fi
"$MF/bin/conda" config --set auto_activate_base false > /dev/null 2>&1 || true
[ -e "$ENVP" ] && echo "environment prefix $ENVP exists - env/install_env.sh refuses to overwrite it (remove it by hand if incomplete)"
CONDA="$MF/bin/conda" bash env/install_env.sh "$ENVP"   # third-batch locked environment; exits 1 when a key package differs (do not run the batch then)
C8=$(cut -c1-8 COMMIT); mkdir -p "$HOME/dfx_hpc"
if [ ! -d "$HOME/dfx_hpc/repo" ]; then
  mkdir "$HOME/dfx_hpc/repo" && tar xzf "code_${C8}.tar.gz" -C "$HOME/dfx_hpc/repo" && cat COMMIT > "$HOME/dfx_hpc/repo/.package_commit"
  echo "code unpacked to $HOME/dfx_hpc/repo (commit $(cat COMMIT))"
else
  echo "$HOME/dfx_hpc/repo exists (commit $(cat "$HOME/dfx_hpc/repo/.package_commit" 2>/dev/null)); package commit $(cat COMMIT)"
fi
[ -e repo ] || ln -s "$HOME/dfx_hpc/repo" repo
echo "home usage: $(du -sh "$HOME" 2>/dev/null | cut -f1) (quota 20 GB); environment: $(du -sh "$ENVP" 2>/dev/null | cut -f1); scratch: $(du -sh "$SCRATCH" 2>/dev/null | cut -f1) (quota 500 GB, 60-day purge)"
echo "next: bash hpc/hpc_preflight.sh (login node), then qsub -v DFX_AUTH=\"<text>\" pbs/dfx_smoke_56.pbs"
