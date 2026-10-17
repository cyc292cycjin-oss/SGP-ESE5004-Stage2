#!/bin/bash
# S4C cloud package builder (run locally in WSL from the repository root after the deployment commit; prepares files only, no cloud action):
#   bash research/06_scope_redesign/p1_step4c_20261016/cloud_package/make_package.sh <builds_dir> <dist_dir>
# builds_dir: the S4C-6 builds (results_project/s4c/s4c6/builds) holding integrated/, disconnected/, integrated_nze/ and disconnected_gap/ with the
#             365x24h networks
# dist_dir:   output folder (outside git), e.g. /mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4c_20261016/cloud_package_dist
# Writes: code_<commit8>.tar.gz (git archive of the whole repository at HEAD, incl. configs/ and research_inputs/), networks/*_365_24h_unsolved.nc
# + build receipts (the NZE network is renamed integrated_nze_365_24h_unsolved.nc), environment files, run/preflight scripts, COMMIT,
# DATA_CONFIG_MANIFEST.json (configs, research inputs, renewable profiles and cutout identity, network build inputs - each with SHA256),
# SHA256SUMS, PACKAGE_MANIFEST.json (incl. total upload size). Never includes the Gurobi licence, the cutout or the LP arrays.
set -euo pipefail
NETS=${1:?builds dir}; DIST=${2:?dist dir}
PKG="$(cd "$(dirname "$0")" && pwd)"
COMMIT=$(git rev-parse HEAD)
if [ -n "$(git status --porcelain --untracked-files=no -- scripts_project configs scripts research_inputs)" ]; then echo "tracked code/config/input changes not committed - commit first"; exit 1; fi
# the networks were built at an earlier commit of the same branch: every later change under the build paths must be outside the build
# (summary / evidence / comparison scripts, tests); anything else -> rebuild the networks at HEAD first
ALLOW='^scripts_project/(s4c_6_summary|s4c_5_compare|s4c_6_collect_evidence)\.py$|^tests/'
for sc in integrated disconnected integrated_nze disconnected_gap; do
  rec=$(ls "$NETS/$sc"/*_BUILD_RECEIPT.json | head -1)
  bsha=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['code_sha'])" "$rec")
  git merge-base --is-ancestor "$bsha" HEAD || { echo "$sc built at $bsha which is not an ancestor of HEAD"; exit 1; }
  changed=$(git diff --name-only "$bsha" HEAD -- scripts_project configs scripts research_inputs | grep -vE "$ALLOW" || true)
  [ -z "$changed" ] || { echo "$sc: build inputs changed since $bsha:"; echo "$changed"; exit 1; }
done
mkdir -p "$DIST/networks"
git archive --format=tar.gz -o "$DIST/code_${COMMIT:0:8}.tar.gz" "$COMMIT"
cp "$NETS/integrated/integrated_365_24h_unsolved.nc" "$NETS/integrated/integrated_BUILD_RECEIPT.json" "$DIST/networks/"
cp "$NETS/disconnected/disconnected_365_24h_unsolved.nc" "$NETS/disconnected/disconnected_BUILD_RECEIPT.json" "$DIST/networks/"
cp "$NETS/integrated_nze/integrated_365_24h_unsolved.nc" "$DIST/networks/integrated_nze_365_24h_unsolved.nc"
cp "$NETS/integrated_nze/integrated_BUILD_RECEIPT.json" "$DIST/networks/integrated_nze_BUILD_RECEIPT.json"
cp "$NETS/disconnected_gap/disconnected_gap_diagnostic_365_24h_unsolved.nc" "$NETS/disconnected_gap/disconnected_gap_diagnostic_BUILD_RECEIPT.json" "$DIST/networks/"
cp "$PKG/run_365x24h.sh" "$PKG/preflight.sh" "$PKG/environment_pypsa-earth.yml" "$PKG/conda_explicit_linux64.txt" "$DIST/"
echo "$COMMIT" > "$DIST/COMMIT"
git ls-files -s -- configs research_inputs > "$DIST/.tracked_inputs.txt"
python3 - "$DIST" "$COMMIT" "$PWD" <<'PY'
import hashlib, json, os, sys
dist, commit, repo = sys.argv[1:4]
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
files = []
for line in open(os.path.join(dist, ".tracked_inputs.txt")):
    meta, path = line.rstrip("\n").split("\t", 1)
    p = os.path.join(repo, path)
    files.append(dict(path=path, bytes=os.path.getsize(p), sha256=sha(p), git_blob=meta.split()[1]))
os.remove(os.path.join(dist, ".tracked_inputs.txt"))
prof = json.load(open(os.path.join(repo, "research_inputs/renewable_v5/MANIFEST.json")))
log = json.load(open(os.path.join(repo, "research_inputs/renewable_v5/S4B3_PROFILES_LOG_c3.json")))
receipts = {}
for f in sorted(os.listdir(os.path.join(dist, "networks"))):
    if f.endswith("_BUILD_RECEIPT.json"):
        r = json.load(open(os.path.join(dist, "networks", f)))
        receipts[f.replace("_BUILD_RECEIPT.json", "")] = dict(code_sha=r.get("code_sha"), status=r.get("status"), scenario=r.get("scenario"), gap_diagnostic=r.get("gap_diagnostic"),
                                                              research_config_sha256=r.get("research_config_sha256"), inputs=r.get("inputs"), network_2920_3h=r.get("network", {}).get("sha256"),
                                                              daily_network=r.get("daily_network"), build_seconds=r.get("build_seconds"))
out = dict(commit=commit,
           note="every file listed under configs_and_research_inputs is inside code_<commit8>.tar.gz (git archive of the commit); the networks are pre-built (no rebuild on the instance); the NZE network carries the build override fuels.price_scenario=nze in its research_config",
           configs_and_research_inputs=files,
           renewable_profiles=dict(main_file="research_inputs/renewable_v5/profiles_calibrated_modern_c3_3h.nc", main_settings="profile_variant calibrated_modern, resource_classes 3 (decisions 74, 75)",
                                   manifest=prof, built_from_cutout=dict(file="cutouts/asean_zenodo_20325289/cutout-2013-era5.nc (NOT in the package)", bytes=7348721462,
                                   sha256="eaa033a328f39c82bbd4c46f74d72b19b7c7f2fcc1056e10b5cdf3a05f0d6f05", source_zip="work/p2_data_intake/raw11/bundle_cutouts_asean.zip",
                                   source_zip_sha256="028ae70154a9a84a696f96788fdf97ecde52ebc16a9c011cd30ebc3567f706df", doi="10.5281/zenodo.20325289", atlite=log.get("atlite"),
                                   cutout_shape=log.get("cutout_shape"))),
           network_builds=receipts)
json.dump(out, open(os.path.join(dist, "DATA_CONFIG_MANIFEST.json"), "w"), indent=1)
print("data/config manifest:", len(files), "files")
PY
( cd "$DIST" && find . -type f ! -name SHA256SUMS ! -name PACKAGE_MANIFEST.json -printf '%P\n' | sort | xargs sha256sum > SHA256SUMS )
python3 - "$DIST" "$COMMIT" <<'PY'
import json, os, sys
dist, commit = sys.argv[1], sys.argv[2]
rows = []
for line in open(os.path.join(dist, "SHA256SUMS")):
    sha, path = line.split(maxsplit=1); path = path.strip()
    rows.append(dict(path=path, sha256=sha, bytes=os.path.getsize(os.path.join(dist, path))))
total = sum(r["bytes"] for r in rows) + os.path.getsize(os.path.join(dist, "SHA256SUMS"))
json.dump(dict(commit=commit, files=rows, upload_total_bytes_excluding_this_manifest=total,
               environment=dict(python="3.11.13", pypsa="0.30.3", linopy="0.5.5", gurobipy="12.0.3", numpy="1.26.4", pandas="2.3.1", xarray="2025.1.2", scipy="1.15.2", netCDF4="1.7.2"),
               run=dict(script="run_365x24h.sh", runs=["integrated (STEPS)", "disconnected (STEPS, extra-ASEAN CO2 storage on)", "integrated_nze (NZE fuel prices)",
                                                      "disconnected_gap (GAP_DIAGNOSTIC; only if the disconnected main ends non-optimal)"],
                        modes=["serial", "lanes2", "lanes3"], solver_profile="REQUIRED --solver-profile, no default (user choice after the S4C-5 recommendation)",
                        kirchhoff_row_normalisation="on (research.solver.scaling.kirchhoff_row_normalisation)", scaling="on",
                        threads_per_run=8, wall_clock_cap_h=3, gurobi_time_limit_s=10500, licence="GRB_LICENSE_FILE supplied by the user on the instance")),
          open(os.path.join(dist, "PACKAGE_MANIFEST.json"), "w"), indent=1)
print("manifest written", len(rows), "files,", total, "bytes")
PY
du -sb "$DIST"; cat "$DIST/SHA256SUMS"
