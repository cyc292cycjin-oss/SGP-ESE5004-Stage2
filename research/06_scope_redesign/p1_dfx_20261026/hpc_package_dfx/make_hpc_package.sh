#!/bin/bash
# DFX phase 2 (PROPOSED, offline draft): assemble the HPC deployment package of the fourth batch on the v2 2920x3h networks in WSL (no HPC
# connection, no solve, no upload). Run from the repository root of the branch with a clean tracked tree:
#   bash research/06_scope_redesign/p1_dfx_20261026/hpc_package_dfx/make_hpc_package.sh <builds_dir> <dist_dir>
# builds_dir: the DFX v2 builds (commit 72083fde; main checkout results_project/dfx_v3/builds_v2) - the two FULL 2920x3h networks (registered SHA256 /
#             bytes below = RUN_PLAN_DFX section 1), their build receipts and cost tables
# dist_dir:   new output folder (never overwritten), e.g. /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/hpc_package_dist
# Writes: code_<commit8>.tar.gz (git archive of HEAD without research/), networks/ (2920x3h + receipts + cost tables; NO 365x24h file), the fourth-batch
# run_batch4.sh + preflight.sh (B4P v7, unchanged), pack_results.sh + env/ (third batch, unchanged), hpc/ (this folder: README, checklist, make_pbs.sh,
# job bodies, install / preflight scripts), pbs/ (generated with the default parameters), RUN_PLAN_B4.md, RUN_PLAN_DFX.md, COMMIT, SHA256SUMS,
# HPC_PACKAGE_MANIFEST.json. Never the licence, the cutout, LP arrays, results, 365x24h networks.
# NOTE (README_HPC section 5-6, checklist B1 / B2): run_batch4.sh / b4_batch4.py still carry the fourth batch's registered v1 inputs (ec80668f) and
# 72 h limits; the manifest records this as "registration_pending" - the package is a draft until the user authorises the re-registration.
set -euo pipefail
B=${1:?builds dir}; DIST=${2:?dist dir}
HPC="$(cd "$(dirname "$0")" && pwd)"; D="$(dirname "$HPC")"; PKG4="$(cd "$HPC/../../p1_b4p_20261026/cloud_package_b4" && pwd)"; PKG3="$(cd "$HPC/../../p1_m10p_20261022/cloud_package" && pwd)"
PY=${PY:-/home/jin/miniforge3/envs/pypsa-earth/bin/python}
COMMIT=$(git rev-parse HEAD); C8=${COMMIT:0:8}; BUILD_COMMIT=72083fde6bffd89580869af6dd00885a8d76721f
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked changes not committed - commit first"; exit 1; }
[ ! -e "$DIST" ] || { echo "dist folder $DIST exists - choose a new one (never overwrite a package)"; exit 1; }
declare -A WANT=([integrated/integrated_2920_3h_unsolved.nc]=08879f0bede119d77160cdb3f5f3c69dba302540b256b64efa4f16adbbefb271
                 [disconnected/disconnected_2920_3h_unsolved.nc]=d90ca99220d448c894c43c071b7e38f8c74e0a101b72878a4bdd941c37b164e7)
declare -A BYTES=([integrated/integrated_2920_3h_unsolved.nc]=63873447 [disconnected/disconnected_2920_3h_unsolved.nc]=63202193)
for f in "${!WANT[@]}"; do
  [ "$(sha256sum "$B/$f" | cut -c1-64)" = "${WANT[$f]}" ] || { echo "$B/$f is not the registered file"; exit 1; }
  [ "$(stat -c %s "$B/$f")" = "${BYTES[$f]}" ] || { echo "$B/$f: byte count differs from the registered value"; exit 1; }
done
for sc in integrated disconnected; do
  [ "$("$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['code_sha'], r['network']['sha256'])" "$B/$sc/${sc}_BUILD_RECEIPT.json")" = "$BUILD_COMMIT ${WANT[$sc/${sc}_2920_3h_unsolved.nc]}" ] || { echo "$sc receipt not from $BUILD_COMMIT or network SHA256 differs"; exit 1; }
done
mkdir -p "$DIST/networks" "$DIST/env" "$DIST/hpc" "$DIST/pbs"
mapfile -t FILES < <(git ls-tree -r --name-only "$COMMIT" | grep -v '^research/')
git --literal-pathspecs archive --format=tar.gz -o "$DIST/code_${C8}.tar.gz" "$COMMIT" -- "${FILES[@]}"
[ "$(tar tzf "$DIST/code_${C8}.tar.gz" | grep -c '[^/]$')" = "${#FILES[@]}" ] || { echo "code archive: file count differs from the list"; exit 1; }
echo "$COMMIT" > "$DIST/COMMIT"
for sc in integrated disconnected; do
  cp "$B/$sc/${sc}_2920_3h_unsolved.nc" "$B/$sc/${sc}_BUILD_RECEIPT.json" "$DIST/networks/"; cp "$B/$sc/costs_active_research.csv" "$DIST/networks/${sc}_costs_active_research.csv"
done
cp "$PKG4/run_batch4.sh" "$PKG4/preflight.sh" "$PKG3/pack_results.sh" "$DIST/"
cp "$PKG3/env/ENV_LOCK.txt" "$PKG3/env/conda_explicit_linux64.txt" "$PKG3/env/pip_only.txt" "$PKG3/env/ENV_DOWNLOAD.json" "$PKG3/env/install_env.sh" "$PKG3/env/env_check.py" "$DIST/env/"
cp "$HPC"/README_HPC.md "$HPC"/HPC_GO_LIVE_CHECKLIST.md "$HPC"/make_pbs.sh "$HPC"/hpc_job_both.sh "$HPC"/hpc_run_one.sh "$HPC"/hpc_batch_post.sh "$HPC"/hpc_smoke_56.sh "$HPC"/hpc_install_env.sh "$HPC"/hpc_preflight.sh "$DIST/hpc/"
cp "$(dirname "$PKG4")/RUN_PLAN_B4.md" "$D/RUN_PLAN_DFX.md" "$DIST/"
( cd "$DIST" && bash hpc/make_pbs.sh pbs > pbs/MAKE_PBS.log )
chmod 755 "$DIST"/*.sh "$DIST/env/install_env.sh" "$DIST/hpc"/*.sh
( cd "$DIST" && find . -type f ! -name SHA256SUMS ! -name HPC_PACKAGE_MANIFEST.json -printf '%P\n' | LC_ALL=C sort | xargs sha256sum > SHA256SUMS )
grep -rIlE "WLSACCESSID|WLSSECRET|LICENSEID" "$DIST" --exclude=hpc_preflight.sh > /dev/null 2>&1 && { echo "LICENCE-LIKE CONTENT IN THE PACKAGE - refused"; exit 1; } || true
"$PY" - "$DIST" "$COMMIT" "$B" "$C8" "$BUILD_COMMIT" <<'P'
import hashlib, json, os, sys, time
sys.path.insert(0, "scripts_project")
import b4_batch4 as B4
dist, commit, b, c8, build = sys.argv[1:6]
rows = []
for line in open(os.path.join(dist, "SHA256SUMS")):
    s, p = line.split(maxsplit=1); p = p.strip(); rows.append(dict(path=p, bytes=os.path.getsize(os.path.join(dist, p)), sha256=s))
sums = os.path.join(dist, "SHA256SUMS"); total = sum(r["bytes"] for r in rows) + os.path.getsize(sums)
nets = {r["path"]: r["sha256"] for r in rows if r["path"].startswith("networks/") and r["path"].endswith(".nc")}
assert not any("365_24h" in p for p in nets), "a 365x24h network is in the package"
h = lambda bps: round(total / bps / 3600, 2)
json.dump(dict(commit=commit, package="HPC draft (fourth batch F1 / F2 on the DFX v2 2920x3h networks; PBS Pro, NUS Atlas)", status="PROPOSED",
               created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files=rows, upload_total_bytes_excluding_this_manifest=total,
               sha256sums_sha256=hashlib.sha256(open(sums, "rb").read()).hexdigest(), upload=dict(method="one rsync / scp stream, then sha256sum -c SHA256SUMS on the login node", hours_at={"1 MB/s": h(1e6), "4 MB/s": h(4e6)}),
               code_archive=dict(file=f"code_{c8}.tar.gz", content=f"git archive of {commit} without the top-level research/ folder"),
               networks=dict(source=f"DFX v2 builds, commit {build[:8]} ({b}); registered in RUN_PLAN_DFX.md section 1", files=nets, no_365x24h=True),
               registration_pending=dict(b4_batch4_registered_sha=B4.REGISTERED_SHA, b4_batch4_build_commit=B4.BUILD_COMMIT, equals_package_networks=(B4.REGISTERED_SHA == {k.split("/")[-1]: v for k, v in nets.items()}),
                                         note="run_batch4.sh phase 0 checks the networks against b4_batch4.py REGISTERED_SHA (fourth batch = v1 networks ec80668f): the v2 networks need the user's re-registration (HPC_GO_LIVE_CHECKLIST B2) and the TimeLimit decision (B1) before a formal run"),
               environment=dict(lock="env/ENV_LOCK.txt", install="env/install_env.sh via hpc/hpc_install_env.sh (miniforge in $HOME, caches on /hpctmp)", check="env/env_check.py"),
               jobs=dict(generator="hpc/make_pbs.sh", generated="pbs/*.pbs (default parameters of HPC_FACTS)", recommended="pbs/dfx_f12_both.pbs (run_batch4.sh as is)", smoke="pbs/dfx_smoke_56.pbs"),
               licence="never in the package; $HOME/.gurobi/gurobi.lic (chmod 600) placed by the user; referenced only through GRB_LICENSE_FILE",
               never_included=["licence", "cutout", "LP / solution arrays", "365x24h networks", "results", "account / host information"]),
          open(os.path.join(dist, "HPC_PACKAGE_MANIFEST.json"), "w"), indent=1)
print("manifest:", len(rows), "files,", total, "bytes; b4_batch4 registered == package networks:", B4.REGISTERED_SHA == {k.split("/")[-1]: v for k, v in nets.items()})
P
du -sb "$DIST"
