#!/bin/bash
# HPR login-node preflight (HPC_OPERATOR_GUIDE.md: after step A upload / step B licence / step C install; no solve, no Gurobi call, nothing of the
# licence printed). Checks: the package SHA256SUMS; the licence file at $HOME/.gurobi/gurobi.lic (existence, owner, mode 600 ONLY); no licence-like
# content inside the package folder; the environment python; the B4P preflight sections guards, sha, networks, env, profile, code, tools (the
# resources and licence sections belong to the jobs); quotas; the queue; the maintenance notice (information: /etc/motd lines with maintenance words).
#   bash hpc/hpr_preflight_login.sh        from the package folder /hpctmp/<user>/hpr
set -u
PKG="$(cd "$(dirname "$0")/.." && pwd)"; cd "$PKG"; ok=1
USER_NAME=${USER:-$(id -un)}; PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}; LIC=${GRB_LICENSE_FILE:-$HOME/.gurobi/gurobi.lic}
echo "== package $PKG (commit $(cat COMMIT 2>/dev/null || echo ?))"
echo "== SHA256SUMS"; sha256sum -c --quiet SHA256SUMS && echo "all $(wc -l < SHA256SUMS) files OK" || { echo "CHECKSUM MISMATCH - re-upload the failed files"; ok=0; }
echo "== licence file (existence, owner, mode only - never read)"
if [ -f "$LIC" ]; then
  mode=$(stat -c %a "$LIC"); owner=$(stat -c %U "$LIC")
  if [ "$mode" = 600 ] && [ "$owner" = "$USER_NAME" ]; then echo "licence file present, owner $owner, mode $mode"; else echo "LICENCE FILE owner/mode wrong: $owner $mode (chmod 600 ~/.gurobi/gurobi.lic)"; ok=0; fi
  case "$LIC" in "$HOME"/.gurobi/*) ;; *) echo "WARNING: the licence is expected at $HOME/.gurobi/gurobi.lic (never inside the package or scratch)";; esac
else echo "LICENCE FILE MISSING at $LIC (step B)"; ok=0; fi
if [ -r "$PKG/hpc/leak_patterns.txt" ]; then   # optional: a pattern file the user may place (never shipped); the package build already refused licence-like content
  pat=$(grep -v '^#' "$PKG/hpc/leak_patterns.txt" | paste -sd '|' -); [ -z "$pat" ] || { grep -rIlE --exclude-dir=repo --exclude-dir=runs --exclude-dir=conda_pkgs_cache --exclude-dir=tmp "$pat" "$PKG" 2>/dev/null | grep -v leak_patterns.txt && { echo "LEAK-LIKE CONTENT INSIDE THE PACKAGE FOLDER"; ok=0; } || echo "no leak-like content in the package folder"; }
fi
echo "== environment python"; [ -x "$PY" ] && echo "python $PY ($("$PY" -c 'import sys; print(sys.version.split()[0])'))" || { echo "environment python missing - run the install job (step C): qsub pbs/hpr_install.pbs"; ok=0; }
if [ -x "$PY" ]; then
  echo "== B4P preflight sections (no resources / licence here)"
  PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools PY="$PY" bash preflight.sh | tail -25; rc=${PIPESTATUS[0]}; [ $rc = 0 ] || ok=0
fi
echo "== quotas"; df -h "$HOME" 2>/dev/null | tail -1; df -h "$PKG" 2>/dev/null | tail -1; du -sh "$HOME" 2>/dev/null; command -v quota > /dev/null 2>&1 && quota -s 2>/dev/null | head -6
echo "== PBS"; command -v qsub > /dev/null 2>&1 && { qstat -Q parallel 2>/dev/null | head -3; qstat -u "$USER_NAME" 2>/dev/null | tail -n +3; } || echo "qsub not on this node?"
echo "== maintenance notice (information; the operator decides - RUN_PLAN_HPC 6)"; grep -iE "maint|downtime|shutdown|outage|schedul" /etc/motd 2>/dev/null | head -10 || echo "(no maintenance words in /etc/motd; check the login banner yourself)"
[ $ok = 1 ] && echo "HPR_PREFLIGHT_LOGIN OK" || { echo "HPR_PREFLIGHT_LOGIN FAILED"; exit 1; }
