#!/bin/bash
# HPR package v9 builder (instruction H5.1): assemble the HPC deployment package of the fourth batch (F1 / F2 on the v2 2920x3h networks, PBS Pro two-job
# method) in WSL from the repository root of the branch with a clean tracked tree; files only (no HPC connection, no solve, no upload).
#   bash research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/make_hpc_package.sh <builds_dir> <dist_dir>
# builds_dir: the DFX v2 builds (commit 72083fde; main checkout results_project/dfx_v3/builds_v2) - the two FULL 2920x3h networks (registered SHA256 /
#             bytes = b4_batch4.py REGISTERED_SHA / REGISTERED_BYTES = RUN_PLAN_HPC section 1), their build receipts and cost tables
# dist_dir:   new output folder (never overwritten), e.g. /mnt/d/ResearchWorkspaces/ASEAN/work/p1_hpr_20261027/hpc_package
# Writes: code_<commit8>.tar.gz (git archive of HEAD without the top-level research/ folder), networks/ (2920x3h + receipts + cost tables; NO 365x24h
# file), run_batch4.sh + preflight.sh (B4P package sources with the HPR amendments), pack_results.sh + env/ (third batch, unchanged), hpc/ (this
# folder: job bodies, make_pbs.sh, install, login preflight, submit, status, consistency), pbs/ (generated from b4_batch4.py hpc-plan), RUN_PLAN_HPC.md,
# HPC_OPERATOR_GUIDE.md, HPC_FACTS_20261026.md (copy), REFERENCE_VALUES.json, COMMIT, SHA256SUMS, HPC_PACKAGE_MANIFEST.json. Never the licence, the
# cutout, LP / solution arrays, results, 365x24h networks, account or host information. H4_JSON = the local H4 drill summary of THIS commit (two
# 56-snapshot runs optimal and bitwise equal to the DFX smoke) is required; H4_SKIP=1 only with the reason recorded in the report.
set -euo pipefail
B=${1:?builds dir}; DIST=${2:?dist dir}
HPC="$(cd "$(dirname "$0")" && pwd)"; D="$(dirname "$HPC")"; ROOT="$(cd "$D/../../.." && pwd)"
PKG4="$ROOT/research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4"; PKG3="$ROOT/research/06_scope_redesign/p1_m10p_20261022/cloud_package"; DFXD="$ROOT/research/06_scope_redesign/p1_dfx_20261026"
PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}
cd "$ROOT"
COMMIT=$(git rev-parse HEAD); C8=${COMMIT:0:8}
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked changes not committed - commit first"; exit 1; }
[ ! -e "$DIST" ] || { echo "dist folder $DIST exists - choose a new one (never overwrite a package)"; exit 1; }
H4_JSON=${H4_JSON:-}; H4_COMMIT=""
if [ "${H4_SKIP:-0}" != 1 ]; then
  [ -n "$H4_JSON" ] && [ -f "$H4_JSON" ] || { echo "REFUSED: H4_JSON=<H4_DRILL.json> is required (instruction H4 / H5.1; H4_SKIP=1 only with a recorded reason)"; exit 1; }
  H4_COMMIT=$("$PY" - "$H4_JSON" <<'P' || exit 1
import json, sys
d = json.load(open(sys.argv[1])); ok = bool(d.get("all_optimal")) and bool(d.get("bitwise_equal_to_dfx_smoke")) and bool(d.get("chain_exit_zero")) and len(str(d.get("code_commit") or "")) == 40
print(d.get("code_commit") if ok else "", file=sys.stdout); print("H4 drill:", "OK" if ok else "REFUSED (not optimal / not bitwise equal / chain error / no commit)", d.get("code_commit"), d.get("all_optimal"), d.get("bitwise_equal_to_dfx_smoke"), file=sys.stderr)
sys.exit(0 if ok else 1)
P
)
  [ -n "$H4_COMMIT" ] || exit 1
  # the drilled execution path must be byte-identical between the drill commit and this commit: the archived code (everything outside research/), the shipped
  # runner / preflight / pack / env sources and the job body + PBS generator; other package sources (guide, plan, submit, status, consistency) may differ
  H4_PATH_DIFF=""
  if [ "$H4_COMMIT" != "$COMMIT" ]; then
    # two pathspecs, compared separately (a git ':(exclude)research' spec would also drop the explicitly listed research/ paths): (1) the archived code that runs
    # on the cluster (everything outside research/; tests/ are archived but never executed there), (2) the shipped scripts of the drilled path
    SHIPPED=(research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4 research/06_scope_redesign/p1_m10p_20261022/cloud_package
             research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/hpr_job.sh research/06_scope_redesign/p1_hpr_20261027/hpc_package_src/make_pbs.sh)
    code_same=0; git diff --quiet "$H4_COMMIT" "$COMMIT" -- . ':(exclude)research' ':(exclude)tests' && code_same=1
    scripts_same=0; git diff --quiet "$H4_COMMIT" "$COMMIT" -- "${SHIPPED[@]}" && scripts_same=1
    if [ $code_same = 1 ] && [ $scripts_same = 1 ]; then echo "H4 drill commit $H4_COMMIT != package commit $COMMIT: the drilled execution path is identical (git diff empty on the archived code outside tests/ and on the runner, preflight, pack, env, job body, PBS generator) - accepted"
    elif [ $code_same = 1 ] && [ "${H4_PATH_DIFF_OK:-0}" = 1 ] && [ -n "${H4_PATH_DIFF_NOTE:-}" ]; then
      # the archived CODE (solve path: scripts_project, model, config) is byte-identical; only shipped bash scripts of the drilled path changed - accepted only with
      # an explicit note (recorded in the manifest with the diff stat); the stand-in tests of the package commit cover the changed scripts
      H4_PATH_DIFF=$( { git diff --stat "$H4_COMMIT" "$COMMIT" -- "${SHIPPED[@]}"; git diff --stat "$H4_COMMIT" "$COMMIT" -- tests; } | tr '\n' ';')
      echo "H4 drill commit $H4_COMMIT != package commit $COMMIT: the archived code is identical; shipped scripts of the drilled path differ (accepted with H4_PATH_DIFF_NOTE): $H4_PATH_DIFF"
    else echo "REFUSED: the drilled execution path changed since the H4 drill commit $H4_COMMIT (archived code identical: $code_same; set H4_PATH_DIFF_OK=1 H4_PATH_DIFF_NOTE=<why> only when it is):"; git diff --stat "$H4_COMMIT" "$COMMIT" -- . ':(exclude)research'; git diff --stat "$H4_COMMIT" "$COMMIT" -- "${SHIPPED[@]}"; exit 1; fi
  fi
fi
export H4_JSON H4_COMMIT H4_PATH_DIFF H4_PATH_DIFF_NOTE=${H4_PATH_DIFF_NOTE:-} H4_SKIP=${H4_SKIP:-0}
# 1. the registered network files (b4_batch4.py = RUN_PLAN_HPC section 1) and their receipts
eval "$("$PY" - <<'P'
import sys; sys.path.insert(0, "scripts_project"); import b4_batch4 as B
print("declare -A WANT=(" + " ".join(f"[{k.split('_')[0]}]={v}" for k, v in B.REGISTERED_SHA.items()) + ")")
print("declare -A BYTES=(" + " ".join(f"[{k.split('_')[0]}]={B.REGISTERED_BYTES[k]}" for k in B.REGISTERED_SHA) + ")")
print(f"BUILD_COMMIT={B.BUILD_COMMIT}")
P
)"
for sc in integrated disconnected; do
  f="$B/$sc/${sc}_2920_3h_unsolved.nc"
  [ "$(sha256sum "$f" | cut -c1-64)" = "${WANT[$sc]}" ] || { echo "$f is not the registered file"; exit 1; }
  [ "$(stat -c %s "$f")" = "${BYTES[$sc]}" ] || { echo "$f: byte count differs from the registered value"; exit 1; }
  [ "$("$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['code_sha'], r['network']['sha256'])" "$B/$sc/${sc}_BUILD_RECEIPT.json")" = "$BUILD_COMMIT ${WANT[$sc]}" ] || { echo "$sc receipt not from $BUILD_COMMIT or network SHA256 differs"; exit 1; }
done
mkdir -p "$DIST/networks" "$DIST/env" "$DIST/hpc" "$DIST/pbs"
# 2. code: git archive of the commit without the top-level research/ folder
mapfile -t FILES < <(git ls-tree -r --name-only "$COMMIT" | grep -v '^research/')
git --literal-pathspecs archive --format=tar.gz -o "$DIST/code_${C8}.tar.gz" "$COMMIT" -- "${FILES[@]}"
[ "$(tar tzf "$DIST/code_${C8}.tar.gz" | grep -c '[^/]$')" = "${#FILES[@]}" ] || { echo "code archive: file count differs from the list"; exit 1; }
echo "$COMMIT" > "$DIST/COMMIT"
# 3. networks (+ receipts, cost tables); never a 365x24h file
for sc in integrated disconnected; do
  cp "$B/$sc/${sc}_2920_3h_unsolved.nc" "$B/$sc/${sc}_BUILD_RECEIPT.json" "$DIST/networks/"; cp "$B/$sc/costs_active_research.csv" "$DIST/networks/${sc}_costs_active_research.csv"
done
# 4. runner / preflight (B4P sources with the HPR amendments), pack, environment (third-batch lock), HPC scripts, plan, guide, facts, reference values
cp "$PKG4/run_batch4.sh" "$PKG4/preflight.sh" "$PKG3/pack_results.sh" "$DIST/"
cp "$PKG3/env/ENV_LOCK.txt" "$PKG3/env/conda_explicit_linux64.txt" "$PKG3/env/pip_only.txt" "$PKG3/env/ENV_DOWNLOAD.json" "$PKG3/env/install_env.sh" "$PKG3/env/env_check.py" "$DIST/env/"
cp "$HPC"/make_pbs.sh "$HPC"/hpr_job.sh "$HPC"/hpr_install_env.sh "$HPC"/hpr_preflight_login.sh "$HPC"/hpr_submit.sh "$HPC"/hpr_status.sh "$HPC"/hpr_consistency.py "$DIST/hpc/"
cp "$D/RUN_PLAN_HPC.md" "$D/HPC_OPERATOR_GUIDE.md" "$D/REFERENCE_VALUES.json" "$D/HPC_FACTS_20261026.md" "$DIST/"   # HPC_FACTS: the copy taken from work/p1_dfx_20261026 (not in the repo's DFX folder)
( cd "$DIST" && REPO="$ROOT" PY="$PY" bash hpc/make_pbs.sh pbs > pbs/MAKE_PBS.log )
chmod 755 "$DIST"/*.sh "$DIST/env/install_env.sh" "$DIST/hpc"/*.sh "$DIST/pbs"/*.pbs
( cd "$DIST" && find . -type f ! -name SHA256SUMS ! -name HPC_PACKAGE_MANIFEST.json -printf '%P\n' | LC_ALL=C sort | xargs sha256sum > SHA256SUMS )
# 5. refusals: licence-like content (patterns read at run time from a file OUTSIDE the repository, never written here), 365x24h files
PF=${LEAK_PATTERN_FILE:-$HOME/.dfx_leak_patterns}
if [ -r "$PF" ]; then
  pat=$(grep -v '^#' "$PF" | grep -E '^key=' | cut -d= -f2-)
  [ -z "$pat" ] || { grep -rIlE "$pat" "$DIST" > /dev/null 2>&1 && { echo "LICENCE-LIKE CONTENT IN THE PACKAGE - refused"; exit 1; } || echo "no licence-like content (pattern file $PF)"; }
else echo "NOTE: pattern file $PF not readable - the licence-like content check is left to the H-P8 leak scan"; fi
ls "$DIST"/networks/*_365_24h_* > /dev/null 2>&1 && { echo "365x24h network in the package - refused"; exit 1; }
# 6. manifest
"$PY" - "$DIST" "$COMMIT" "$B" "$C8" <<'P'
import hashlib, json, os, sys, time
sys.path.insert(0, "scripts_project")
import b4_batch4 as B
dist, commit, b, c8 = sys.argv[1:5]
rows = []
for line in open(os.path.join(dist, "SHA256SUMS")):
    s, p = line.split(maxsplit=1); p = p.strip(); rows.append(dict(path=p, bytes=os.path.getsize(os.path.join(dist, p)), sha256=s))
sums = os.path.join(dist, "SHA256SUMS"); total = sum(r["bytes"] for r in rows) + os.path.getsize(sums)
nets = {r["path"]: r["sha256"] for r in rows if r["path"].startswith("networks/") and r["path"].endswith(".nc")}
assert nets == {f"networks/{k}": v for k, v in B.REGISTERED_SHA.items()}, "network SHA256 differ from the registered values"
assert not any("365_24h" in p for p in nets), "a 365x24h network is in the package"
env = json.load(open(os.path.join(dist, "env", "ENV_DOWNLOAD.json")))
h = lambda bps: round(total / bps / 3600, 2)
h4 = os.environ.get("H4_JSON")
json.dump(dict(commit=commit, package="v9 (HPR: fourth batch F1 / F2 on the DFX v2 2920x3h networks; NUS Atlas PBS Pro, two-job method)", created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               files=rows, upload_total_bytes_excluding_this_manifest=total, sha256sums_sha256=hashlib.sha256(open(sums, "rb").read()).hexdigest(),
               upload=dict(method="PowerShell scp of the whole folder to /hpctmp/<user>/hpr/, then sha256sum -c SHA256SUMS on the login node; a failed file re-sent alone, then the full check again",
                           hours_at={"1 MB/s": h(1e6), "4 MB/s": h(4e6), "10 MB/s": h(10e6)}),
               code_archive=dict(file=f"code_{c8}.tar.gz", content=f"git archive of {commit} without the top-level research/ folder"),
               networks=dict(source=f"DFX v2 builds, commit {B.BUILD_COMMIT[:8]} (main checkout results_project/dfx_v3/{os.path.basename(b)}); registered in RUN_PLAN_HPC.md section 1 = b4_batch4.py", files=nets, registered=B.REGISTERED_SHA, registered_bytes=B.REGISTERED_BYTES, no_365x24h=True),
               environment=dict(lock="env/ENV_LOCK.txt", explicit="env/conda_explicit_linux64.txt", pip_only="env/pip_only.txt", install="pbs/hpr_install.pbs -> hpc/hpr_install_env.sh -> env/install_env.sh (compute node; caches on scratch)", check="env/env_check.py",
                                download_bytes=env["download_bytes"], conda_packages=env["conda_packages"], same_lock_as="third batch (M10P), fourth-batch package v7, DFX package v8"),
               run=dict(plan="RUN_PLAN_HPC.md", runner="run_batch4.sh (--only per job; POST_ONLY=1 batch job)", preflight=["preflight.sh (in-job, no licence section)", "hpc/hpr_preflight_login.sh"], pack="pack_results.sh",
                        jobs=B.HPC_JOBS, time_limit_s=B.TIME_LIMIT_S, wall_cap_s=B.WALL_CAP_S, licence_gap_s=B.LICENCE_GAP_S, wait_start_max_s=B.WAIT_START_MAX_S, smoke=B.SMOKE,
                        thresholds=dict(memory_stop_fraction=B.MEMORY_STOP_FRACTION, projection_fraction=B.PROJECTION_FRACTION, iterations_reference={k: v["iterations_reference"] for k, v in B.RUNS.items()}),
                        solve_mode="split (process 1 s2_solve.py --split-stage build, process 2 b4_split_solve.py, process 3 s2_solve.py --split-stage assign)",
                        licence="GRB_LICENSE_FILE=$HOME/.gurobi/gurobi.lic placed by the user; never in the package; referenced only by the jobs"),
               operator_guide="HPC_OPERATOR_GUIDE.md", facts="HPC_FACTS_20261026.md", reference_values="REFERENCE_VALUES.json (numbers only: third batch R3 / R4, R1 / R2; DFX V1 / V2)",
               never_included=["licence", "cutout", "LP / solution arrays", "365x24h networks", "results", "account / host / connection information"],
               h4_drill=(dict(file=os.path.basename(h4), sha256=hashlib.sha256(open(h4, "rb").read()).hexdigest(), **{k: json.load(open(h4)).get(k) for k in ("code_commit", "all_optimal", "bitwise_equal_to_dfx_smoke", "chain_exit_zero", "written_utc")},
                              drilled_path_identical_to_package_commit=(not os.environ.get("H4_PATH_DIFF")), drilled_path_diff_stat=(os.environ.get("H4_PATH_DIFF") or None), path_diff_note=(os.environ.get("H4_PATH_DIFF_NOTE") or None),
                              note=("drill commit = package commit" if os.environ.get("H4_COMMIT") == commit else ("the drill commit differs from the package commit only outside the drilled execution path (git diff empty on the archived code, runner, preflight, pack, env, job body, PBS generator)" if not os.environ.get("H4_PATH_DIFF") else "the archived code is identical to the drill commit; shipped scripts of the drilled path changed after the drill (see drilled_path_diff_stat / path_diff_note; covered by the stand-in tests of the package commit)")))
                         if h4 and os.path.exists(h4) else dict(skipped=True, reason="H4_SKIP=1 (see the report)"))),
          open(os.path.join(dist, "HPC_PACKAGE_MANIFEST.json"), "w"), indent=1)
print("manifest:", len(rows), "files,", total, "bytes")
P
du -sb "$DIST"
