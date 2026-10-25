#!/bin/bash
# M10P non-clone environment install (instruction section 4.3; S4N supplement 01 B2 / B3 practice) on a fresh instance with conda (Miniconda /
# Miniforge). Exact conda builds from the explicit lock (no solving, md5 checked by conda), then the PyPI-only packages, then the per-package check
# against ENV_LOCK.txt (key packages must be identical, otherwise exit 1 - do not run the batch).
#
#   bash install_env.sh [env prefix]        default prefix /root/autodl-tmp/envs/pypsa-earth (data disk); CONDA=<conda binary>
#   bash install_env.sh --check-mirrors     B4P A3.3: only the mirror URL format and reachability checks below (no environment is created)
#   optional mirrors (B4P A3.3, M10 finding 6: no Chinese mirror carries the gurobi channel, so a whole-prefix replacement could not be used):
#     CONDA_MIRROR_CONDA_FORGE=<base url of the conda-forge channel, e.g. https://mirrors.example.edu/anaconda/cloud/conda-forge>
#     CONDA_MIRROR_BIOCONDA=<base url of the bioconda channel>    CONDA_MIRROR_GUROBI=<base url of the gurobi channel>
#       each set channel has its URL prefix https://conda.anaconda.org/<channel>/ replaced in the explicit list; an unset channel stays direct;
#     CONDA_MIRROR=<base url replacing https://conda.anaconda.org> (the earlier whole-prefix form; used only when no per-channel variable is set);
#     PIP_INDEX_URL=<pip index>
#   Before conda create, every replaced channel is checked lightly: the first two package URLs of the channel are fetched with curl as a 1 KB
#   range request (--max-time 20, no full download); a failure prints MIRROR_CHECK_FAILED:<channel>:<url> and stops with exit 2, success prints
#   MIRROR_OK:<channel>. A base URL that is not http(s)://... prints MIRROR_URL_INVALID and stops with exit 2.
#
# Download ~743 MB (538 conda packages, ENV_DOWNLOAD.json) + 2 small PyPI packages; installed ~3.3 GiB. Expected 5-15 min at 2-20 MB/s
# (download + extraction); stop and report if the download would exceed 2 GB or the install 30 min (S4N supplement 01 B2.3).
# The licence is not touched. An existing prefix is never overwritten or removed.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CHECK_ONLY=0; [ "${1:-}" = --check-mirrors ] && { CHECK_ONLY=1; shift; }
ENVP=${1:-/root/autodl-tmp/envs/pypsa-earth}
ORIGIN=https://conda.anaconda.org
CHANNELS="conda-forge bioconda gurobi"
mirror_of() {   # $1 channel -> the per-channel base URL ("" = not set)
  case "$1" in
    conda-forge) echo "${CONDA_MIRROR_CONDA_FORGE:-}";;
    bioconda) echo "${CONDA_MIRROR_BIOCONDA:-}";;
    gurobi) echo "${CONDA_MIRROR_GUROBI:-}";;
  esac
}
per_channel_set() { local c; for c in $CHANNELS; do [ -n "$(mirror_of "$c")" ] && return 0; done; return 1; }
mirror_base() {   # $1 channel -> effective base URL of the channel after the replacement ("" = direct)
  local m; m=$(mirror_of "$1")
  if per_channel_set; then echo "${m%/}"; elif [ -n "${CONDA_MIRROR:-}" ]; then echo "${CONDA_MIRROR%/}/$1"; else echo ""; fi
}
make_spec() {   # $1 original explicit list $2 output: the list with every mirrored channel's prefix replaced; prints MIRROR / DIRECT lines; exit 2 on a bad URL
  local src=$1 dst=$2 c base
  cp "$src" "$dst"
  for c in $CHANNELS; do
    base=$(mirror_base "$c")
    if [ -z "$base" ]; then echo "DIRECT:$c:$ORIGIN/$c"; continue; fi
    case "$base" in
      http://*|https://*) [ "${base//[[:space:]]/}" = "$base" ] || { echo "MIRROR_URL_INVALID:$c:$base"; return 2; };;
      *) echo "MIRROR_URL_INVALID:$c:$base (http:// or https:// base URL expected)"; return 2;;
    esac
    sed -i "s#$ORIGIN/$c/#$base/#" "$dst"; echo "MIRROR:$c:$base"
  done
  return 0
}
check_mirrors() {   # $1 mirrored explicit list: the first two package URLs of every replaced channel fetched as a 1 KB range (no full download)
  local spec=$1 c base urls u n checked=0
  command -v curl > /dev/null 2>&1 || { echo "MIRROR_CHECK_FAILED:curl missing (apt-get install -y curl)"; return 2; }
  for c in $CHANNELS; do
    base=$(mirror_base "$c"); [ -n "$base" ] || continue
    urls=$(grep -E "^$base/" "$spec" | sed 's/#.*$//' | head -2); n=0
    [ -n "$urls" ] || { echo "MIRROR_CHECK_FAILED:$c:no package URL of this channel in the list"; return 2; }
    for u in $urls; do
      if curl -sSf -r 0-1023 --max-time 20 --max-filesize 2097152 -o /dev/null "$u" > /dev/null 2>&1; then n=$((n + 1)); else echo "MIRROR_CHECK_FAILED:$c:$u"; return 2; fi
    done
    echo "MIRROR_OK:$c:$n urls reachable (1 KB range requests)"; checked=$((checked + 1))
  done
  [ $checked -gt 0 ] || echo "MIRROR_CHECK:none (every channel direct from $ORIGIN)"
  return 0
}
if [ "$CHECK_ONLY" = 1 ]; then
  [ -s "$HERE/conda_explicit_linux64.txt" ] || { echo "REFUSED: conda_explicit_linux64.txt missing"; exit 2; }
  make_spec "$HERE/conda_explicit_linux64.txt" "$HERE/.explicit_mirror.txt" || exit 2
  check_mirrors "$HERE/.explicit_mirror.txt" || exit 2
  echo "MIRROR_CHECK_DONE (no environment created)"; exit 0
fi
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
if per_channel_set || [ -n "${CONDA_MIRROR:-}" ]; then
  SPEC="$HERE/.explicit_mirror.txt"
  make_spec "$HERE/conda_explicit_linux64.txt" "$SPEC" | tee -a "$LOG"; rc=${PIPESTATUS[0]}; [ "$rc" = 0 ] || { echo "MIRROR_URL_INVALID (see above; nothing downloaded, no environment created)" | tee -a "$LOG"; exit 2; }
  check_mirrors "$SPEC" | tee -a "$LOG"; rc=${PIPESTATUS[0]}; [ "$rc" = 0 ] || { echo "MIRROR_CHECK_FAILED (see above; nothing downloaded, no environment created)" | tee -a "$LOG"; exit 2; }
else
  echo "MIRROR_CHECK:none (every channel direct from $ORIGIN)" | tee -a "$LOG"
fi
"$CONDA" create -y -p "$ENVP" --file "$SPEC" >> "$LOG" 2>&1 || { echo "CONDA_CREATE_FAILED (see $LOG)"; exit 1; }
echo "CONDA_DONE:$(( $(date +%s) - t0 ))s" | tee -a "$LOG"
"$ENVP/bin/python" -m pip install --no-deps ${PIP_INDEX_URL:+-i "$PIP_INDEX_URL"} -r "$HERE/pip_only.txt" >> "$LOG" 2>&1 || { echo "PIP_FAILED (see $LOG)"; exit 1; }
echo "PIP_DONE:$(( $(date +%s) - t0 ))s" | tee -a "$LOG"
"$ENVP/bin/python" "$HERE/env_check.py" "$HERE/ENV_LOCK.txt" --out "$HERE/ENV_CHECK.json" | tee -a "$LOG"; rc=${PIPESTATUS[0]}
echo "INSTALL_END:$(date -u +%FT%TZ):seconds=$(( $(date +%s) - t0 )):size=$(du -sh "$ENVP" 2>/dev/null | cut -f1):key_packages_identical=$([ "$rc" = 0 ] && echo yes || echo NO)" | tee -a "$LOG"
for t in /usr/bin/time setsid tmux pgrep; do command -v "$t" >/dev/null 2>&1 || echo "MISSING TOOL $t (apt-get install -y time util-linux tmux procps)" | tee -a "$LOG"; done
echo "next: PY=$ENVP/bin/python bash ../preflight.sh" | tee -a "$LOG"
exit "$rc"
