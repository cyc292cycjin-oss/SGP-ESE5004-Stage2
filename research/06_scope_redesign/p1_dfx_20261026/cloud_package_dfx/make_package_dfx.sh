#!/bin/bash
# DFX package builder (instruction v3 F6.3; deployment package v8 of the DFX 365x24h screening; derived from the B4P make_package.sh): run in WSL
# from the repository root of the branch with a clean tracked tree; prepares files only (no cloud action, no solve, no upload).
#   bash research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx/make_package_dfx.sh <builds_dir> <dist_dir>
# builds_dir: the DFX v2 builds (commit 72083fde; main checkout results_project/dfx_v3/builds_v2) - the two 365x24h networks with the registered
#             SHA256 (RUN_PLAN_DFX section 1), their build receipts and cost tables
# dist_dir:   new output folder (never overwritten), e.g. /mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_package_dfx
# Writes: code_<commit8>.tar.gz (git archive of HEAD without the top-level research/ folder, as the third-batch packages), networks/ (365x24h
# integrated / disconnected + receipts + cost tables; NO 2920x3h network), run_dfx.sh, preflight_dfx.sh, pack_results.sh (third batch), env/ (the
# third-batch lock, explicit conda list, PyPI list, install and check scripts), RUN_PLAN_DFX.md, BATCH3_REFERENCE_VALUES.json, BUILD_INPUT_CHANGES.json,
# COMMIT, SHA256SUMS, PACKAGE_MANIFEST.json. Never the licence, the cutout, LP arrays, results, 2920x3h networks. DRY_RUN_JSON = the DRY_RUN_DFX.json of
# this commit (local dry run of run_dfx.sh: BUILD_ONLY on the two networks, BUILD_CHECK passed, refusals checked) is required; DRY_SKIP=1 only with the
# reason recorded in the report.
set -euo pipefail
B=${1:?builds dir}; DIST=${2:?dist dir}
PKG="$(cd "$(dirname "$0")" && pwd)"; D="$(dirname "$PKG")"; PKG3="$(cd "$PKG/../../p1_m10p_20261022/cloud_package" && pwd)"
PY=${PY:-/home/jin/miniforge3/envs/pypsa-earth/bin/python}
COMMIT=$(git rev-parse HEAD); C8=${COMMIT:0:8}; BUILD_COMMIT=72083fde6bffd89580869af6dd00885a8d76721f
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked changes not committed - commit first"; exit 1; }
[ ! -e "$DIST" ] || { echo "dist folder $DIST exists - choose a new one (never overwrite a package)"; exit 1; }
DRY_RUN_JSON=${DRY_RUN_JSON:-}
if [ "${DRY_SKIP:-0}" != 1 ]; then
  [ -n "$DRY_RUN_JSON" ] && [ -f "$DRY_RUN_JSON" ] || { echo "REFUSED: DRY_RUN_JSON=<DRY_RUN_DFX.json of commit $C8> is required (instruction F6.3; DRY_SKIP=1 only with a recorded reason)"; exit 1; }
  "$PY" - "$DRY_RUN_JSON" "$COMMIT" <<'P' || exit 1
import json, sys
d = json.load(open(sys.argv[1])); ok = bool(d.get("passed")) and d.get("code_commit") == sys.argv[2] and {"V1", "V2"} <= set(d.get("build_check") or {})
print("dry run:", "OK" if ok else "REFUSED (not passed, another commit, or a run missing)", d.get("code_commit"), sorted(d.get("build_check") or {}))
sys.exit(0 if ok else 1)
P
fi
export DRY_RUN_JSON DRY_SKIP=${DRY_SKIP:-0}
# 1. the registered network files (RUN_PLAN_DFX section 1) and their receipts
declare -A WANT=([integrated/integrated_365_24h_unsolved.nc]=82928a4c9151a6a176ac8c81bf56bbe41867e16ba0d059ce2ad8c6e78e59f6b2
                 [disconnected/disconnected_365_24h_unsolved.nc]=5c75bfa0e338fde4104deb41cdcaa72dddcf7b3782e6ad8ca1f4fb6c15cfbd5c)
declare -A BYTES=([integrated/integrated_365_24h_unsolved.nc]=31292240 [disconnected/disconnected_365_24h_unsolved.nc]=30620986)
for f in "${!WANT[@]}"; do
  [ "$(sha256sum "$B/$f" | cut -c1-64)" = "${WANT[$f]}" ] || { echo "$B/$f is not the registered file"; exit 1; }
  [ "$(stat -c %s "$B/$f")" = "${BYTES[$f]}" ] || { echo "$B/$f: byte count differs from the registered value"; exit 1; }
done
for sc in integrated disconnected; do
  [ "$("$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['code_sha'], r['daily_network']['sha256'])" "$B/$sc/${sc}_BUILD_RECEIPT.json")" = "$BUILD_COMMIT ${WANT[$sc/${sc}_365_24h_unsolved.nc]}" ] || { echo "$sc receipt not from $BUILD_COMMIT or daily network SHA256 differs"; exit 1; }
done
mkdir -p "$DIST/networks" "$DIST/env"
# 2. build inputs unchanged since the build commit (import closure of scripts_project/s2_network.py; as the third-batch and B4P packages)
"$PY" - "$BUILD_COMMIT" "$COMMIT" "$DIST/BUILD_INPUT_CHANGES.json" <<'P'
import ast, json, subprocess, sys
b, h, out = sys.argv[1:4]
git = lambda *a: subprocess.run(["git", *a], check=True, capture_output=True, text=True).stdout
have = {p[len("scripts_project/"):-3] for p in git("ls-tree", "-r", "--name-only", h, "scripts_project").split() if p.endswith(".py") and p.count("/") == 1}
seen, todo = set(), ["s2_network"]
while todo:
    m = todo.pop()
    if m in seen or m not in have:
        continue
    seen.add(m)
    for node in ast.walk(ast.parse(git("show", f"{h}:scripts_project/{m}.py"))):
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
        todo += [n.split(".")[0] for n in names]
changed = [p for p in git("diff", "--name-only", b, h, "--", "scripts_project", "configs", "scripts", "research_inputs").split() if p]
rows, refused = [], []
for p in changed:
    mod = p[len("scripts_project/"):-3] if p.startswith("scripts_project/") and p.endswith(".py") and p.count("/") == 1 else None
    if p.startswith(("configs/", "research_inputs/")):
        why = "config / input changed"; refused.append(p)
    elif mod is not None and mod in seen:
        why = "imported by the build"; refused.append(p)
    elif p.startswith("scripts_project/") and p.endswith((".py", ".sh")) and p.count("/") == 1:
        why = "not imported by the build (import closure of scripts_project/s2_network.py)"
    else:
        why = "outside the build path"; refused.append(p)
    rows.append(dict(path=p, classification=why))
json.dump(dict(build_commit=b, head=h, changed=rows, refused=refused, build_modules=sorted(seen), note="the networks are taken from the build commit; refused changes would require a rebuild"), open(out, "w"), indent=1)
print("build inputs:", "OK" if not refused else "REFUSED", len(changed), "changed files")
sys.exit(1 if refused else 0)
P
# 3. code: git archive of the commit without the top-level research/ folder
mapfile -t FILES < <(git ls-tree -r --name-only "$COMMIT" | grep -v '^research/')
git --literal-pathspecs archive --format=tar.gz -o "$DIST/code_${C8}.tar.gz" "$COMMIT" -- "${FILES[@]}"
[ "$(tar tzf "$DIST/code_${C8}.tar.gz" | grep -c '[^/]$')" = "${#FILES[@]}" ] || { echo "code archive: file count differs from the list"; exit 1; }
echo "$COMMIT" > "$DIST/COMMIT"
# 4. networks (+ receipts, cost tables); never a 2920x3h file
for sc in integrated disconnected; do
  cp "$B/$sc/${sc}_365_24h_unsolved.nc" "$B/$sc/${sc}_BUILD_RECEIPT.json" "$DIST/networks/"; cp "$B/$sc/costs_active_research.csv" "$DIST/networks/${sc}_costs_active_research.csv"
done
# 5. scripts, environment (the third-batch lock: the environment is unchanged), plan, third-batch reference values
cp "$PKG/run_dfx.sh" "$PKG/preflight_dfx.sh" "$DIST/"; cp "$PKG3/pack_results.sh" "$DIST/"
cp "$PKG3/env/ENV_LOCK.txt" "$PKG3/env/conda_explicit_linux64.txt" "$PKG3/env/pip_only.txt" "$PKG3/env/ENV_DOWNLOAD.json" "$PKG3/env/install_env.sh" "$PKG3/env/env_check.py" "$DIST/env/"
cp "$D/RUN_PLAN_DFX.md" "$D/BATCH3_REFERENCE_VALUES.json" "$DIST/"
chmod 755 "$DIST"/*.sh "$DIST/env/install_env.sh"
( cd "$DIST" && find . -type f ! -name SHA256SUMS ! -name PACKAGE_MANIFEST.json -printf '%P\n' | LC_ALL=C sort | xargs sha256sum > SHA256SUMS )
# 6. manifest
"$PY" - "$DIST" "$COMMIT" "$B" "$C8" <<'P'
import hashlib, json, os, sys, time
sys.path.insert(0, "scripts_project")
from dfx_batch import RUNS, REGISTERED_SHA, REGISTERED_BYTES, TIME_LIMIT_S, WALL_MARGIN_S, LICENCE_GAP_S, PARALLEL_MIN_CORES, BUILD_COMMIT
dist, commit, b, c8 = sys.argv[1:5]
rows = []
for line in open(os.path.join(dist, "SHA256SUMS")):
    s, p = line.split(maxsplit=1); p = p.strip(); rows.append(dict(path=p, bytes=os.path.getsize(os.path.join(dist, p)), sha256=s))
sums = os.path.join(dist, "SHA256SUMS"); total = sum(r["bytes"] for r in rows) + os.path.getsize(sums)
env = json.load(open(os.path.join(dist, "env", "ENV_DOWNLOAD.json")))
nets = {r["path"]: r["sha256"] for r in rows if r["path"].startswith("networks/") and r["path"].endswith(".nc")}
assert nets == {f"networks/{k}": v for k, v in REGISTERED_SHA.items()}, "network SHA256 differ from the registered values"
assert not any("2920_3h" in p for p in nets), "a 2920x3h network is in the package"
h = lambda bps: round(total / bps / 3600, 2)
dr = os.environ.get("DRY_RUN_JSON")
json.dump(dict(commit=commit, package="v8 (DFX 365x24h screening, v2 demand networks)", created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files=rows, upload_total_bytes_excluding_this_manifest=total,
               sha256sums_sha256=hashlib.sha256(open(sums, "rb").read()).hexdigest(),
               upload=dict(method="ONE rsync stream into the package folder, then sha256sum -c SHA256SUMS; a failed file re-sent alone, then the full check again; the licence only after every file is OK",
                           hours_at={"36 KB/s": h(36e3), "100 KB/s": h(100e3), "318 KB/s": h(318e3)}, note="KB = 1000 B"),
               code_archive=dict(file=f"code_{c8}.tar.gz", content=f"git archive of {commit} without the top-level research/ folder"),
               networks=dict(source=f"DFX v2 builds, commit {BUILD_COMMIT[:8]} ({b}); registered SHA256 / bytes in RUN_PLAN_DFX.md section 1", files=nets, registered=REGISTERED_SHA, registered_bytes=REGISTERED_BYTES,
                             no_2920x3h=True, build_input_changes="BUILD_INPUT_CHANGES.json"),
               environment=dict(lock="env/ENV_LOCK.txt", explicit="env/conda_explicit_linux64.txt", pip_only="env/pip_only.txt", install="env/install_env.sh (per-channel mirrors: CONDA_MIRROR_CONDA_FORGE / _BIOCONDA / _GUROBI; --check-mirrors)", check="env/env_check.py",
                                download_bytes=env["download_bytes"], conda_packages=env["conda_packages"], same_lock_as="third batch (M10P) and fourth-batch package v7"),
               run=dict(plan="RUN_PLAN_DFX.md", script="run_dfx.sh", preflight="preflight_dfx.sh", pack="pack_results.sh", reference_values="BATCH3_REFERENCE_VALUES.json",
                        runs={k: {x: v[x] for x in ("scenario", "base", "set", "profile", "costs")} for k, v in RUNS.items()},
                        time_limit_s=TIME_LIMIT_S, wall_cap_s={k: v + WALL_MARGIN_S for k, v in TIME_LIMIT_S.items()}, licence_gap_s=LICENCE_GAP_S, parallel_min_cores=PARALLEL_MIN_CORES,
                        solve_mode="single process (s2_solve.py, as the third batch)", licence="GRB_LICENSE_FILE supplied by the user on the instance; never in the package"),
               never_included=["licence", "cutout", "LP / solution arrays", "2920x3h networks", "results"],
               dry_run=(dict(file=dr, sha256=hashlib.sha256(open(dr, "rb").read()).hexdigest(), **{k: json.load(open(dr)).get(k) for k in ("code_commit", "passed", "written_utc")})
                        if dr and os.path.exists(dr) else dict(skipped=True, reason="DRY_SKIP=1 (see the report)"))),
          open(os.path.join(dist, "PACKAGE_MANIFEST.json"), "w"), indent=1)
print("manifest:", len(rows), "files,", total, "bytes")
P
du -sb "$DIST"
