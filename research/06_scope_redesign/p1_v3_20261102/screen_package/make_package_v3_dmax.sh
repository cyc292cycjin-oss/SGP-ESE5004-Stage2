#!/bin/bash
# V3 screening RERUN package builder (supplement 07, decision 182; review EVDIAG section 2.1 item 6; derived from make_package_v3.sh, which stays as it was for the first screening package):
# three runs V1 -> V2 -> V3 on the networks rebuilt with the daily max of the Store e_min_pu. Run in WSL from the repository root with a clean tracked tree; prepares files only (no cloud action, no solve, no upload).
#   DRY_RUN_JSON=<DRY_RUN_SCREEN.json of this commit> bash research/06_scope_redesign/p1_v3_20261102/screen_package/make_package_v3_dmax.sh <builds_dir> <dist_dir>
# builds_dir: results_project/v3/builds_dmax; dist_dir: new output folder (never overwritten). Writes code_<commit8>.tar.gz (git archive of HEAD without the top-level research/ folder), networks/ (integrated, no_new_xb,
# disconnected 365x24h, their receipts, the two cost tables; NO bridge and NO 2920x3h network), BATCH_DEF.json (= batch_def/BATCH_DEF_365x24h_dmax.json), run_dfx.sh, preflight_dfx.sh, pack_results.sh, env/,
# RUN_PLAN_SCREEN_V3.md, V3_RULES.md, BUILD_INPUT_CHANGES.json, COMMIT, SHA256SUMS, PACKAGE_MANIFEST.json. Never the licence, the cutout, LP arrays, results.
set -euo pipefail
B=${1:?builds dir}; DIST=${2:?dist dir}
HERE="$(cd "$(dirname "$0")" && pwd)"; D="$(dirname "$HERE")"; R6="$(dirname "$D")"; PKG="$R6/p1_dfx_20261026/cloud_package_dfx"; PKG3="$R6/p1_m10p_20261022/cloud_package"
PY=${PY:-/home/jin/miniforge3/envs/pypsa-earth/bin/python}; DEF="$D/batch_def/BATCH_DEF_365x24h_dmax.json"
COMMIT=$(git rev-parse HEAD); C8=${COMMIT:0:8}
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked changes not committed - commit first"; exit 1; }
[ ! -e "$DIST" ] || { echo "dist folder $DIST exists - choose a new one (never overwrite a package)"; exit 1; }
DRY_RUN_JSON=${DRY_RUN_JSON:?DRY_RUN_JSON=<DRY_RUN_SCREEN.json of this commit> is required}
"$PY" - "$DRY_RUN_JSON" "$COMMIT" <<'P'
import json, sys
d = json.load(open(sys.argv[1])); ok = bool(d.get("passed")) and d.get("code_commit") == sys.argv[2] and set(d.get("build_check") or {}) == {"V1", "V2", "V3"}
print("dry run:", "OK" if ok else "REFUSED (not passed, another commit, or not the three runs)", d.get("code_commit"), sorted(d.get("build_check") or {}))
sys.exit(0 if ok else 1)
P
BUILD_COMMIT=$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1]))['build_commit'])" "$DEF")
mkdir -p "$DIST/networks" "$DIST/env"
# 1. the registered files under their package names; build inputs unchanged since the build commit (import closure of scripts_project/s2_network.py)
"$PY" - "$DEF" "$B" "$DIST/networks" <<'P'
import hashlib, json, shutil, sys
from pathlib import Path
d = json.load(open(sys.argv[1])); B, N = Path(sys.argv[2]), Path(sys.argv[3]); sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
SRC = {"integrated_365_24h_unsolved.nc": "integrated/integrated_365_24h_unsolved.nc", "no_new_xb_365_24h_unsolved.nc": "no_new_xb/no_new_xb_365_24h_unsolved.nc", "disconnected_365_24h_unsolved.nc": "disconnected/disconnected_365_24h_unsolved.nc"}
if set(SRC) != set(d["registered_sha"]):
    sys.exit("the definition does not register exactly the three networks")
for k, f in SRC.items():
    p = B / f
    if sha(p) != d["registered_sha"][k] or p.stat().st_size != d["registered_bytes"][k]:
        sys.exit(f"{p} is not the registered file")
    shutil.copy2(p, N / k)
for k, f in (("integrated", "integrated/integrated_BUILD_RECEIPT.json"), ("disconnected", "disconnected/disconnected_BUILD_RECEIPT.json")):
    r = json.load(open(B / f)); key = f"{k}_365_24h_unsolved.nc"
    if r["code_sha"] != d["build_commit"] or r["daily_network"]["sha256"] != d["registered_sha"][key]:
        sys.exit(f"{f}: code or daily network differs from the definition")
    shutil.copy2(B / f, N / f"{k}_BUILD_RECEIPT.json")
v = json.load(open(B / "no_new_xb/no_new_xb_365_24h_VARIANT_RECEIPT.json"))
if v["output"]["sha256"] != d["registered_sha"]["no_new_xb_365_24h_unsolved.nc"] or v["base"]["sha256"] != d["registered_sha"]["integrated_365_24h_unsolved.nc"]:
    sys.exit("variant receipt differs from the definition")
shutil.copy2(B / "no_new_xb/no_new_xb_365_24h_VARIANT_RECEIPT.json", N)
shutil.copy2(B / "integrated/costs_active_research.csv", N / "integrated_costs_active_research.csv"); shutil.copy2(B / "disconnected/costs_active_research.csv", N / "disconnected_costs_active_research.csv")
print("networks OK", len(SRC))
P
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
    if p.startswith(("configs/", "research_inputs/")) or (mod is not None and mod in seen):
        refused.append(p); why = "build input changed"
    elif p.startswith("scripts_project/"):
        why = "not imported by the build"
    else:
        refused.append(p); why = "outside the build path"
    rows.append(dict(path=p, classification=why))
json.dump(dict(build_commit=b, head=h, changed=rows, refused=refused, build_modules=sorted(seen)), open(out, "w"), indent=1)
print("build inputs:", "OK" if not refused else "REFUSED", len(changed), "changed files")
sys.exit(1 if refused else 0)
P
# 2. code: git archive of the commit without the top-level research/ folder
mapfile -t FILES < <(git ls-tree -r --name-only "$COMMIT" | grep -v '^research/')
git --literal-pathspecs archive --format=tar.gz -o "$DIST/code_${C8}.tar.gz" "$COMMIT" -- "${FILES[@]}"
[ "$(tar tzf "$DIST/code_${C8}.tar.gz" | grep -c '[^/]$')" = "${#FILES[@]}" ] || { echo "code archive: file count differs from the list"; exit 1; }
echo "$COMMIT" > "$DIST/COMMIT"
# 3. scripts, definition, environment (third-batch lock: unchanged), plans
cp "$PKG/run_dfx.sh" "$PKG/preflight_dfx.sh" "$PKG3/pack_results.sh" "$DIST/"; cp "$DEF" "$DIST/BATCH_DEF.json"
cp "$PKG3/env/ENV_LOCK.txt" "$PKG3/env/conda_explicit_linux64.txt" "$PKG3/env/pip_only.txt" "$PKG3/env/ENV_DOWNLOAD.json" "$PKG3/env/install_env.sh" "$PKG3/env/env_check.py" "$DIST/env/"
cp "$D/RUN_PLAN_SCREEN_V3.md" "$D/V3_RULES.md" "$DIST/"
chmod 755 "$DIST"/*.sh "$DIST/env/install_env.sh"
( cd "$DIST" && find . -type f ! -name SHA256SUMS ! -name PACKAGE_MANIFEST.json -printf '%P\n' | LC_ALL=C sort | xargs sha256sum > SHA256SUMS )
# 4. manifest
"$PY" - "$DIST" "$COMMIT" "$B" "$C8" "$DRY_RUN_JSON" <<'P'
import hashlib, json, os, sys, time
dist, commit, b, c8, dr = sys.argv[1:6]
d = json.load(open(os.path.join(dist, "BATCH_DEF.json"))); rows = []
for line in open(os.path.join(dist, "SHA256SUMS")):
    s, p = line.split(maxsplit=1); p = p.strip(); rows.append(dict(path=p, bytes=os.path.getsize(os.path.join(dist, p)), sha256=s))
sums = os.path.join(dist, "SHA256SUMS"); total = sum(r["bytes"] for r in rows) + os.path.getsize(sums)
nets = {r["path"]: r["sha256"] for r in rows if r["path"].startswith("networks/") and r["path"].endswith(".nc")}
assert nets == {f"networks/{k}": v for k, v in d["registered_sha"].items()}, "network SHA256 differ from the registered values"
assert not any("2920_3h" in r["path"] or "bridge_" in r["path"] for r in rows), "a 2920x3h or bridge file is in the package"
h = lambda bps: round(total / bps / 3600, 2)
json.dump(dict(commit=commit, package="V3 365x24h screening rerun after decision 182 (supplement 07), three runs V1 -> V2 -> V3", created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files=rows, upload_total_bytes_excluding_this_manifest=total,
               sha256sums_sha256=hashlib.sha256(open(sums, "rb").read()).hexdigest(), upload=dict(method="NOT UPLOADED. Later: ONE rsync stream, then sha256sum -c SHA256SUMS; the licence only after every file is OK", hours_at={"36 KB/s": h(36e3), "100 KB/s": h(100e3), "318 KB/s": h(318e3), "1.36 MB/s": h(1.36e6)}),
               code_archive=dict(file=f"code_{c8}.tar.gz", content=f"git archive of {commit} without the top-level research/ folder"), networks=dict(source=f"commit {d['build_commit'][:8]} ({b})", files=nets, registered_bytes=d["registered_bytes"], no_2920x3h=True, no_bridge=True),
               run=dict(plan="RUN_PLAN_SCREEN_V3.md section 10", rules="V3_RULES.md section 11", script="run_dfx.sh", preflight="preflight_dfx.sh", pack="pack_results.sh", definition="BATCH_DEF.json", runs=d["runs"], schedule=d["schedule"], time_limit_s=d["time_limit_s"], licence="GRB_LICENSE_FILE supplied by the user on the instance; never in the package"),
               never_included=["licence", "cutout", "LP / solution arrays", "2920x3h networks", "bridge networks", "results"], dry_run=dict(file=dr, sha256=hashlib.sha256(open(dr, "rb").read()).hexdigest(), **{k: json.load(open(dr)).get(k) for k in ("code_commit", "passed", "written_utc")})),
          open(os.path.join(dist, "PACKAGE_MANIFEST.json"), "w"), indent=1, ensure_ascii=False)
print("manifest:", len(rows), "files,", total, "bytes")
P
du -sb "$DIST"
