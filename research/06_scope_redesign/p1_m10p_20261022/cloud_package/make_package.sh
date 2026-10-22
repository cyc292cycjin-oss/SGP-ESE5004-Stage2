#!/bin/bash
# M10P package builder (instruction section 4): run in WSL from the repository root of the integration branch with a clean tracked tree; prepares
# files only (no cloud action, no solve).
#   bash research/06_scope_redesign/p1_m10p_20261022/cloud_package/make_package.sh <builds_dir> <dist_dir> <work_dir>
# builds_dir: the M08b supplement 01 builds (commit ec80668f; main checkout results_project/m08b/builds_s01) - user decision 2026-10-22 (A): the
#             package takes these files; the M10P-2 rebuild at b46fc23d is content-identical (only n.meta s2_layers.geothermal.bus_mapping_source.path,
#             the build-worktree path, differs) and is the check.
# dist_dir:   new output folder (never overwritten), e.g. /mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/cloud_package_dist
# work_dir:   scratch folder for the two variant passes (outside git), e.g. <main checkout>/results_project/m10p/package_variants
# Writes: code_<commit8>.tar.gz (git archive of HEAD), networks/ (365x24h integrated / disconnected, 2920x3h integrated for P1, build receipts, cost
# tables), EXPECTED_VARIANTS.json (+ VARIANT_REPRODUCIBILITY.json: two local passes byte-identical), run / pack / preflight scripts, env/ (lock,
# explicit conda list, PyPI list, install and check scripts), RUN_PLAN.md, BUILD_INPUT_CHANGES.json, NETWORK_REBUILD_CHECK.json, COMMIT,
# SHA256SUMS, PACKAGE_MANIFEST.json (every file with SHA256). Never the licence, the cutout, LP arrays or variant networks.
set -euo pipefail
B=${1:?builds dir}; DIST=${2:?dist dir}; WORK=${3:?work dir}
PKG="$(cd "$(dirname "$0")" && pwd)"; D="$(dirname "$PKG")"
PY=${PY:-/home/jin/miniforge3/envs/pypsa-earth/bin/python}
COMMIT=$(git rev-parse HEAD); C8=${COMMIT:0:8}; BUILD_COMMIT=ec80668fbd14742565e189fa368fbee8b8f29242
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked changes not committed - commit first"; exit 1; }
[ ! -e "$DIST" ] || { echo "dist folder $DIST exists - choose a new one (never overwrite a package)"; exit 1; }
[ ! -e "$WORK" ] || { echo "work folder $WORK exists - choose a new one"; exit 1; }
# 1. the registered network files (M08b supplement 01 section 8.5) and their receipts
declare -A WANT=([integrated/integrated_365_24h_unsolved.nc]=75704334dc11deeb06fc80f84ef197d65c3ac5bd658ab450e4ee1a93a3ccb19e
                 [disconnected/disconnected_365_24h_unsolved.nc]=888a009b5f19eb34f7f1c24e36f7c8370617a9c405b1097a9caed0599cecbee4
                 [integrated/integrated_2920_3h_unsolved.nc]=bca20fc08a149772074b620e1f587e86b0306c29e81d138fa67f4a9b9ae53cab)
for f in "${!WANT[@]}"; do [ "$(sha256sum "$B/$f" | cut -c1-64)" = "${WANT[$f]}" ] || { echo "$B/$f is not the registered file"; exit 1; }; done
for sc in integrated disconnected; do
  [ "$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1]))['code_sha'])" "$B/$sc/${sc}_BUILD_RECEIPT.json")" = "$BUILD_COMMIT" ] || { echo "$sc receipt not from $BUILD_COMMIT"; exit 1; }
done
mkdir -p "$DIST/networks" "$DIST/env"
# 2. build inputs unchanged since the build commit: configs/ and research_inputs/ identical; every changed scripts_project / scripts file is outside
#    the import closure of the build entry scripts_project/s2_network.py (as S4O package_checks.py build-inputs)
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
res = dict(build_commit=b, head=h, changed=rows, refused=refused, build_modules=sorted(seen),
           note="the networks are taken from the build commit; refused changes would require a rebuild. Empirical check: M10P-2 rebuilt the four networks at b46fc23d - every component table and time series identical (NETWORK_REBUILD_CHECK.json)")
json.dump(res, open(out, "w"), indent=1)
print("build inputs:", "OK" if not refused else "REFUSED", len(changed), "changed files")
sys.exit(1 if refused else 0)
P
# 3. code
git archive --format=tar.gz -o "$DIST/code_${C8}.tar.gz" "$COMMIT"
echo "$COMMIT" > "$DIST/COMMIT"
# 4. networks (+ receipts, cost tables)
cp "$B/integrated/integrated_365_24h_unsolved.nc" "$B/integrated/integrated_2920_3h_unsolved.nc" "$B/integrated/integrated_BUILD_RECEIPT.json" "$DIST/networks/"
cp "$B/disconnected/disconnected_365_24h_unsolved.nc" "$B/disconnected/disconnected_BUILD_RECEIPT.json" "$DIST/networks/"
for sc in integrated disconnected; do cp "$B/$sc/costs_active_research.csv" "$DIST/networks/${sc}_costs_active_research.csv"; done
# 5. the seven variants twice from the package networks (PYTHONHASHSEED=0, code of HEAD): byte-identical -> EXPECTED_VARIANTS.json
for pass in 1 2; do
  mkdir -p "$WORK/pass$pass"
  while IFS='|' read -r rid sc base set prof costs; do
    [ -n "$set" ] || continue
    extra=(); [ "${set%%=*}" = finance.wacc_mode ] && extra=(--costs "$DIST/networks/${costs}_costs_active_research.csv")
    PYTHONHASHSEED=0 "$PY" scripts_project/m08a_variants.py --repo . --base "$DIST/networks/${base}_unsolved.nc" --out "$WORK/pass$pass/$rid" --set "$set" "${extra[@]}" > "$WORK/pass$pass/$rid.log" 2>&1 \
      || { echo "variant $rid pass $pass failed: $(tail -3 "$WORK/pass$pass/$rid.log" 2>/dev/null)"; exit 1; }
  done < <("$PY" scripts_project/m10_batch3_summary.py runtable)
  "$PY" scripts_project/m10_batch3_summary.py variants-expected --variants "$WORK/pass$pass" --out "$WORK/EXPECTED_pass$pass.json"
done
"$PY" - "$WORK" "$DIST" <<'P'
import json, sys
from pathlib import Path
w, d = Path(sys.argv[1]), Path(sys.argv[2])
p1, p2 = json.loads((w / "EXPECTED_pass1.json").read_text()), json.loads((w / "EXPECTED_pass2.json").read_text())
rows = {r: dict(pass1=p1[r]["output_sha256"], pass2=p2.get(r, {}).get("output_sha256"), equal=p1[r]["output_sha256"] == p2.get(r, {}).get("output_sha256"),
                output_file=p1[r]["output_file"], bytes=p1[r]["output_bytes"], stale_config=p1[r]["stale_config"]) for r in sorted(p1)}
ok = len(rows) == 7 and all(v["equal"] and v["stale_config"] is False for v in rows.values())
(d / "VARIANT_REPRODUCIBILITY.json").write_text(json.dumps(dict(passes=2, variants=rows, all_equal=ok, note="m08a_variants.py from the package networks with the code of the package commit, PYTHONHASHSEED=0, without --allow-stale-base"), indent=1) + "\n")
(d / "EXPECTED_VARIANTS.json").write_text(json.dumps(p1, indent=1, sort_keys=True) + "\n")
print("variants reproducible:", ok); sys.exit(0 if ok else 1)
P
# 6. scripts, environment, plan, checks
cp "$PKG/run_batch3.sh" "$PKG/pack_results.sh" "$PKG/preflight.sh" "$DIST/"
cp "$PKG/env/ENV_LOCK.txt" "$PKG/env/conda_explicit_linux64.txt" "$PKG/env/pip_only.txt" "$PKG/env/ENV_DOWNLOAD.json" "$PKG/env/install_env.sh" "$PKG/env/env_check.py" "$DIST/env/"
cp "$D/RUN_PLAN.md" "$DIST/"
cp "$D/evidence/M10P_NETWORK_CONTENT_DIFF.json" "$DIST/NETWORK_REBUILD_CHECK.json"
chmod 755 "$DIST"/*.sh "$DIST/env/install_env.sh"
( cd "$DIST" && find . -type f ! -name SHA256SUMS ! -name PACKAGE_MANIFEST.json -printf '%P\n' | LC_ALL=C sort | xargs sha256sum > SHA256SUMS )
# 7. manifest (every file with SHA256)
"$PY" - "$DIST" "$COMMIT" "$B" <<'P'
import json, os, sys, time
sys.path.insert(0, "scripts_project")
from m10_batch3_summary import RUNS
dist, commit, b = sys.argv[1:4]
rows = []
for line in open(os.path.join(dist, "SHA256SUMS")):
    s, p = line.split(maxsplit=1); p = p.strip(); rows.append(dict(path=p, bytes=os.path.getsize(os.path.join(dist, p)), sha256=s))
total = sum(r["bytes"] for r in rows) + os.path.getsize(os.path.join(dist, "SHA256SUMS"))
env = json.load(open(os.path.join(dist, "env", "ENV_DOWNLOAD.json")))
h = lambda bps: round(total / bps / 3600, 2)
json.dump(dict(commit=commit, created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files=rows, upload_total_bytes_excluding_this_manifest=total,
               upload=dict(method="ONE rsync stream into the package folder, then sha256sum -c SHA256SUMS (every file); a failed file is re-sent alone, then the full check again; the licence only after every file is OK (cloud_upload_single_stream practice)",
                           hours_at={"36 KB/s (S4O-6 AutoDL clone, upload)": h(36e3), "0.16 MB/s (S4N link)": h(0.16e6), "4 MB/s (L23 same region)": h(4e6)}),
               networks=dict(source=f"M08b supplement 01 builds, commit ec80668f ({b}); user decision 2026-10-22 (A)", rebuild_check="NETWORK_REBUILD_CHECK.json: M10P-2 rebuild at b46fc23d - data identical, only n.meta s2_layers.geothermal.bus_mapping_source.path (build-worktree path) differs",
                             files={r["path"]: r["sha256"] for r in rows if r["path"].startswith("networks/") and r["path"].endswith(".nc")}, build_input_changes="BUILD_INPUT_CHANGES.json"),
               variants=dict(expected="EXPECTED_VARIANTS.json", reproducibility="VARIANT_REPRODUCIBILITY.json", generated_on_the_instance=True, uploaded=False, count=7),
               environment=dict(lock="env/ENV_LOCK.txt", explicit="env/conda_explicit_linux64.txt", pip_only="env/pip_only.txt", install="env/install_env.sh", check="env/env_check.py",
                                download_bytes=env["download_bytes"], conda_packages=env["conda_packages"], expected_install_minutes="5-15 at 2-20 MB/s (INFERENCE)",
                                key=dict(python="3.11.13", pypsa="0.30.3", linopy="0.5.5", xarray="2025.1.2", pandas="2.3.1", numpy="1.26.4", scipy="1.15.2", gurobipy="12.0.3",
                                         netCDF4="1.7.2", h5netcdf="1.6.4", dask="2025.7.0", pyomo="6.9.3", highspy="1.11.0")),
               run=dict(plan="RUN_PLAN.md", script="run_batch3.sh", preflight="preflight.sh", pack="pack_results.sh", runs={k: {x: v[x] for x in ("scenario", "base", "set", "profile")} for k, v in RUNS.items()},
                        licence="GRB_LICENSE_FILE supplied by the user on the instance; never in the package"),
               never_included=["licence", "cutout", "LP / solution arrays", "variant networks (generated on the instance)", "results"]),
          open(os.path.join(dist, "PACKAGE_MANIFEST.json"), "w"), indent=1)
print("manifest:", len(rows), "files,", total, "bytes")
P
du -sb "$DIST"
