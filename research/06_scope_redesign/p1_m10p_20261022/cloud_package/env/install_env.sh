#!/bin/bash
# M10P non-clone environment install (instruction section 4.3; S4N supplement 01 B2 / B3 practice) on a fresh instance with conda (Miniconda /
# Miniforge). Exact conda builds from the explicit lock (no solving, md5 checked by conda), then the PyPI-only packages, then the per-package check
# against ENV_LOCK.txt (key packages must be identical, otherwise exit 1 - do not run the batch).
#
#   bash install_env.sh [env prefix]        default prefix /root/autodl-tmp/envs/pypsa-earth (data disk); CONDA=<conda binary>
#   optional mirrors: CONDA_MIRROR=<base url replacing https://conda.anaconda.org> (e.g. a university mirror), PIP_INDEX_URL=<pip index>
#
# Download ~743 MB (538 conda packages, ENV_DOWNLOAD.json) + 2 small PyPI packages; installed ~3.3 GiB. Expected 5-15 min at 2-20 MB/s
# (download + extraction); stop and report if the download would exceed 2 GB or the install 30 min (S4N supplement 01 B2.3).
# The licence is not touched. An existing prefix is never overwritten or removed.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ENVP=${1:-/root/autodl-tmp/envs/pypsa-earth}
# M10A (B5.4): the conda package cache (~0.75 GB tarballs + ~3.3 GB extracted) and temporary files go to the package folder on the data disk, not to
# the conda root / /tmp on the ~30 GB system disk (a cache on the same file system as the prefix is hard-linked, not copied)
export CONDA_PKGS_DIRS="${CONDA_PKGS_DIRS:-$HERE/../conda_pkgs_cache}"; export TMPDIR="${TMPDIR:-$HERE/../tmp}"; export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$TMPDIR/pip_cache}"
mkdir -p "$CONDA_PKGS_DIRS" "$TMPDIR" "$PIP_CACHE_DIR"
CONDA=${CONDA:-$(command -v conda || command -v mamba || echo /root/miniconda3/bin/conda)}
[ -x "$CONDA" ] || { echo "REFUSED: conda not found (set CONDA=<path to conda>)"; exit 2; }
[ -e "$ENVP" ] && { echo "REFUSED: $ENVP exists (never overwritten; choose another prefix)"; exit 2; }
for f in conda_explicit_linux64.txt pip_only.txt ENV_LOCK.txt env_check.py; do [ -s "$HERE/$f" ] || { echo "REFUSED: $f missing"; exit 2; }; done
LOG="$HERE/INSTALL_$(date -u +%Y%m%dT%H%M%SZ).log"; t0=$(date +%s)
echo "INSTALL_START:$(date -u +%FT%TZ):prefix=$ENVP:conda=$("$CONDA" --version 2>&1):pkgs_dirs=$CONDA_PKGS_DIRS:tmpdir=$TMPDIR" | tee -a "$LOG"
SPEC="$HERE/conda_explicit_linux64.txt"
if [ -n "${CONDA_MIRROR:-}" ]; then SPEC="$HERE/.explicit_mirror.txt"; sed "s#https://conda.anaconda.org/#${CONDA_MIRROR%/}/#" "$HERE/conda_explicit_linux64.txt" > "$SPEC"; echo "CONDA_MIRROR:${CONDA_MIRROR}" | tee -a "$LOG"; fi
"$CONDA" create -y -p "$ENVP" --file "$SPEC" >> "$LOG" 2>&1 || { echo "CONDA_CREATE_FAILED (see $LOG)"; exit 1; }
echo "CONDA_DONE:$(( $(date +%s) - t0 ))s" | tee -a "$LOG"
"$ENVP/bin/python" -m pip install --no-deps ${PIP_INDEX_URL:+-i "$PIP_INDEX_URL"} -r "$HERE/pip_only.txt" >> "$LOG" 2>&1 || { echo "PIP_FAILED (see $LOG)"; exit 1; }
echo "PIP_DONE:$(( $(date +%s) - t0 ))s" | tee -a "$LOG"
"$ENVP/bin/python" "$HERE/env_check.py" "$HERE/ENV_LOCK.txt" --out "$HERE/ENV_CHECK.json" | tee -a "$LOG"; rc=${PIPESTATUS[0]}
echo "INSTALL_END:$(date -u +%FT%TZ):seconds=$(( $(date +%s) - t0 )):size=$(du -sh "$ENVP" 2>/dev/null | cut -f1):key_packages_identical=$([ "$rc" = 0 ] && echo yes || echo NO)" | tee -a "$LOG"
for t in /usr/bin/time setsid tmux pgrep; do command -v "$t" >/dev/null 2>&1 || echo "MISSING TOOL $t (apt-get install -y time util-linux tmux procps)" | tee -a "$LOG"; done
echo "next: PY=$ENVP/bin/python bash ../preflight.sh" | tee -a "$LOG"
exit "$rc"
