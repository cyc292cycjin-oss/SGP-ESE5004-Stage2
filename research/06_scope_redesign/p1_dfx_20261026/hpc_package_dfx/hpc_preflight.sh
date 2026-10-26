#!/bin/bash
# DFX phase 2 (PROPOSED, offline draft): login-node preflight of the HPC package (no solve, no licence use, nothing of the licence printed).
#   bash hpc/hpc_preflight.sh              from the package folder on scratch ($HPCTMP/dfx_hpc/package)
# Checks: licence file existence / owner / mode 600 only; paths (scratch, repo link, environment python); SHA256SUMS of the package; the two 2920x3h
# v2 networks against the DFX-registered SHA256 / bytes (RUN_PLAN_DFX section 1) and their build receipts; environment key packages (env/env_check.py);
# tools needed by run_batch4.sh (GNU time, setsid, timeout, pgrep) - NOTE: the compute nodes may differ from the login node, the smoke job repeats the
# tool check; quotas (home 20 GB, scratch 500 GB); the maintenance window is a go-live item (HPC_GO_LIVE_CHECKLIST.md). WLS reachability is checked
# by the smoke job on a compute node, not here.
set -u
PKG="$(cd "$(dirname "$0")/.." && pwd)"; cd "$PKG"; ok=1
USER_NAME=${USER:-$(id -un)}; SCRATCH=${HPCTMP:-/hpctmp/$USER_NAME}/dfx_hpc; PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}
LIC=${GRB_LICENSE_FILE:-$HOME/.gurobi/gurobi.lic}
echo "== licence file (existence, owner, mode only)"
if [ -f "$LIC" ]; then
  mode=$(stat -c %a "$LIC"); owner=$(stat -c %U "$LIC")
  [ "$mode" = 600 ] && [ "$owner" = "$USER_NAME" ] && echo "licence file present, owner $owner, mode $mode" || { echo "LICENCE FILE mode/owner wrong: $owner $mode (chmod 600, own file)"; ok=0; }
  case "$LIC" in "$HOME"/.gurobi/*) ;; *) echo "WARNING: the licence is expected at $HOME/.gurobi/gurobi.lic (never inside the package / scratch)";; esac
else echo "LICENCE FILE MISSING at $LIC"; ok=0; fi
grep -rIl --exclude-dir=repo --exclude-dir=runs -E "WLS(ACCESS[I]D|SECRE[T])|LICENSE[I]D=" "$PKG" 2>/dev/null && { echo "LICENCE-LIKE CONTENT INSIDE THE PACKAGE FOLDER - remove it"; ok=0; } || echo "no licence-like content in the package folder"   # pattern written so that this file itself does not match
echo "== paths"
[ -d "$SCRATCH" ] && echo "scratch $SCRATCH present" || { echo "scratch $SCRATCH missing (mkdir -p)"; ok=0; }
[ -x "$PY" ] && echo "environment python $PY" || { echo "environment python missing: run hpc/hpc_install_env.sh"; ok=0; }
[ -d repo ] && [ "$(cat repo/.package_commit 2>/dev/null)" = "$(cat COMMIT)" ] && echo "./repo = commit $(cat COMMIT)" || { echo "./repo missing or another commit (hpc_install_env.sh)"; ok=0; }
echo "== SHA256SUMS"; sha256sum -c --quiet SHA256SUMS && echo "all $(wc -l < SHA256SUMS) files OK" || { echo "CHECKSUM MISMATCH"; ok=0; }
echo "== networks (2920x3h v2; DFX-registered values + build receipts)"
"$PY" - "$PKG/networks" <<'P' || ok=0
import hashlib, json, sys
from pathlib import Path
nets = Path(sys.argv[1])
REG = {"integrated_2920_3h_unsolved.nc": ("08879f0bede119d77160cdb3f5f3c69dba302540b256b64efa4f16adbbefb271", 63873447),
       "disconnected_2920_3h_unsolved.nc": ("d90ca99220d448c894c43c071b7e38f8c74e0a101b72878a4bdd941c37b164e7", 63202193)}
BUILD = "72083fde6bffd89580869af6dd00885a8d76721f"; good = True
for name, (s, b) in REG.items():
    f = nets / name; rec = json.load(open(nets / f"{name.split('_')[0]}_BUILD_RECEIPT.json"))
    have = hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None
    ok = have == s and f.stat().st_size == b and rec["network"]["sha256"] == s and rec["code_sha"] == BUILD
    print(name, "OK" if ok else "DIFFERENT", (have or "missing")[:16], f.stat().st_size if f.exists() else None, "receipt", rec["network"]["sha256"][:16], rec["code_sha"][:8]); good = good and ok
extra = sorted(p.name for p in nets.glob("*_365_24h_*"))
if extra:
    print("365x24h files present (not part of the fourth batch):", extra); good = False
sys.exit(0 if good else 1)
P
echo "== environment vs env/ENV_LOCK.txt"; "$PY" env/env_check.py env/ENV_LOCK.txt --out "$PKG/HPC_ENV_CHECK.json" || { echo "KEY PACKAGES DIFFER"; ok=0; }
echo "== tools (login node; the smoke job repeats this on a compute node)"
for t in /usr/bin/time setsid timeout pgrep curl; do
  if [ "$t" = /usr/bin/time ]; then [ -x /usr/bin/time ] && /usr/bin/time -v true > /dev/null 2>&1 && echo "GNU time present" || { echo "MISSING GNU time at /usr/bin/time (ask the admins or build it in \$HOME)"; ok=0; }
  else command -v "$t" > /dev/null 2>&1 && echo "$t present" || { echo "MISSING $t"; ok=0; }; fi
done
echo "== quotas"; df -h "$HOME" | tail -1; df -h "$SCRATCH" 2>/dev/null | tail -1; du -sh "$HOME" 2>/dev/null; command -v quota > /dev/null 2>&1 && quota -s 2>/dev/null | head -5
echo "== PBS"; command -v qsub > /dev/null 2>&1 && qstat -Q parallel 2>/dev/null | head -3 || echo "qsub not on this node?"
[ $ok = 1 ] && echo "HPC_PREFLIGHT OK (WLS reachability + compute-node tools: smoke job)" || { echo "HPC_PREFLIGHT FAILED"; exit 1; }
