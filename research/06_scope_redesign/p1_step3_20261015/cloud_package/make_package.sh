#!/bin/bash
# S3B cloud package builder (run locally in WSL from the repository root after the deployment commit):
#   bash research/06_scope_redesign/p1_step3_20261015/cloud_package/make_package.sh <networks_dir> <dist_dir>
# networks_dir: the S3B smoke builds (results_project/s3b/smoke/builds) holding integrated/ and disconnected/ (main, origin_neutral)
# dist_dir:     output folder (outside git), e.g. /mnt/d/ResearchWorkspaces/ASEAN/work/p1_step3_20261015/cloud_package_dist
# Writes: code_<commit>.tar.gz (git archive of the whole repository at HEAD), networks/*_365_24h_unsolved.nc + build receipts,
# environment files, run/preflight scripts, COMMIT, SHA256SUMS, PACKAGE_MANIFEST.json. Never includes the Gurobi licence.
set -euo pipefail
NETS=${1:?networks dir}; DIST=${2:?dist dir}
PKG="$(cd "$(dirname "$0")" && pwd)"
COMMIT=$(git rev-parse HEAD)
if [ -n "$(git status --porcelain --untracked-files=no -- scripts_project configs scripts research_inputs)" ]; then echo "tracked code/config/input changes not committed - commit first"; exit 1; fi
mkdir -p "$DIST/networks"
git archive --format=tar.gz -o "$DIST/code_${COMMIT:0:8}.tar.gz" "$COMMIT"
for sc in integrated disconnected; do
  cp "$NETS/$sc/${sc}_365_24h_unsolved.nc" "$DIST/networks/"
  cp "$NETS/$sc/${sc}_BUILD_RECEIPT.json" "$DIST/networks/"
done
cp "$PKG/run_365x24h.sh" "$PKG/preflight.sh" "$PKG/environment_pypsa-earth.yml" "$PKG/conda_explicit_linux64.txt" "$DIST/"
echo "$COMMIT" > "$DIST/COMMIT"
( cd "$DIST" && find . -type f ! -name SHA256SUMS ! -name PACKAGE_MANIFEST.json -printf '%P\n' | sort | xargs sha256sum > SHA256SUMS )
python3 - "$DIST" "$COMMIT" <<'PY'
import json, os, sys, hashlib
dist, commit = sys.argv[1], sys.argv[2]
rows = []
for line in open(os.path.join(dist, "SHA256SUMS")):
    sha, path = line.split(maxsplit=1); path = path.strip()
    rows.append(dict(path=path, sha256=sha, bytes=os.path.getsize(os.path.join(dist, path))))
rec = {}
for sc in ["integrated", "disconnected"]:
    r = json.load(open(os.path.join(dist, "networks", f"{sc}_BUILD_RECEIPT.json")))
    rec[sc] = {k: r.get(k) for k in ["code_sha", "research_config_sha256", "scenario", "status"] if k in r}
json.dump(dict(commit=commit, files=rows, network_build_receipts=rec,
               environment=dict(python="3.11.13", pypsa="0.30.3", linopy="0.5.5", gurobipy="12.0.3", numpy="1.26.4", pandas="2.3.1", xarray="2025.1.2", scipy="1.15.2", netCDF4="1.7.2"),
               run=dict(script="run_365x24h.sh", scenarios=["integrated", "disconnected"], fuel_carbon_mode="origin_neutral", solver_profile="formal_barrier", scaling="on",
                        threads_per_scenario=8, wall_clock_cap_h=3, gurobi_time_limit_s=10500, licence="GRB_LICENSE_FILE supplied by the user on the instance")),
          open(os.path.join(dist, "PACKAGE_MANIFEST.json"), "w"), indent=1)
print("manifest written", len(rows), "files")
PY
du -sh "$DIST"; cat "$DIST/SHA256SUMS"
