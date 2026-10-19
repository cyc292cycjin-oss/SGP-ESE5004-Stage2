#!/bin/bash
# S4M cloud package builder (S4M-3, decision 116; run locally in WSL from the repository root after the S4M final code commit; prepares files only, no
# cloud action):
#   bash research/06_scope_redesign/p1_step4m_20261019/cloud_package/make_package.sh <builds_dir> <dist_dir> <smoke_solves_dir>
# builds_dir:       the S4M-1 builds at the final code commit (results_project/s4m/s4m1/builds) holding integrated/, disconnected/, integrated_nze/ and
#                   disconnected_gap/ with the 2920x3h and 365x24h networks
# dist_dir:         output folder (outside git), e.g. /mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4m_20261019/cloud_package_dist
# smoke_solves_dir: the S4M-2 smoke solves (results_project/s4m/s4m2/solves) - the local reference of the speed probe (s4m_A_integrated)
# Writes: code_<commit8>.tar.gz (git archive of the whole repository at HEAD), networks/*_365_24h_unsolved.nc + build receipts (the NZE network is renamed
# integrated_nze_365_24h_unsolved.nc), networks/integrated_56_3h_probe_unsolved.nc (first 56 snapshots of the integrated 2920x3h network: the speed probe),
# PROBE_REFERENCE.json, environment files, run / preflight / speed_probe scripts, COMMIT, DATA_CONFIG_MANIFEST.json, SHA256SUMS, PACKAGE_MANIFEST.json.
# Never includes the Gurobi licence, the cutout or the LP arrays.
set -euo pipefail
NETS=${1:?builds dir}; DIST=${2:?dist dir}; SMOKE=${3:?smoke solves dir}
PKG="$(cd "$(dirname "$0")" && pwd)"
COMMIT=$(git rev-parse HEAD)
if [ -n "$(git status --porcelain --untracked-files=no -- scripts_project configs scripts research_inputs)" ]; then echo "tracked code/config/input changes not committed - commit first"; exit 1; fi
# the networks were built at an earlier commit of the same branch: every later change under the build paths must be outside the build
# (summary / evidence / comparison scripts, tests); anything else -> rebuild the networks at HEAD first
ALLOW='^scripts_project/(s4k_[3-5]_[a-z_]+|s4l_[0-9]_[a-z_]+|s4m_[2-9]_[a-z_]+)\.py$|^tests/'
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
for tag in integrated disconnected integrated_nze disconnected_gap; do cp "$NETS/$tag/costs_active_research.csv" "$DIST/networks/${tag}_costs_active_research.csv"; done   # S4M supplement 01: the build cost tables for the per-run cost breakdown export
cp "$PKG/run_365x24h.sh" "$PKG/preflight.sh" "$PKG/speed_probe.sh" "$PKG/environment_pypsa-earth.yml" "$PKG/conda_explicit_linux64.txt" "$DIST/"
echo "$COMMIT" > "$DIST/COMMIT"
# speed probe network (first 56 snapshots of the integrated 2920x3h network) and the local reference from the S4M-2 integrated smoke
PYTHONHASHSEED=0 python3 - "$NETS/integrated/integrated_2920_3h_unsolved.nc" "$DIST/networks/integrated_56_3h_probe_unsolved.nc" "$SMOKE/s4m_A_integrated" "$DIST/PROBE_REFERENCE.json" <<'PY'
import json, re, sys, logging, platform
import pypsa
logging.getLogger("pypsa").setLevel(logging.ERROR)
src, dst, smoke, ref_out = sys.argv[1:5]
n = pypsa.Network(src); n.set_snapshots(n.snapshots[:56]); n.meta["speed_probe"] = dict(source="first 56 snapshots of integrated_2920_3h_unsolved.nc", purpose="S4M-3 speed probe (SMOKE_TEST_ONLY)")
n.export_to_netcdf(dst)
rec = json.load(open(f"{smoke}/SOLVE_RECEIPT.json")); it = sec = wu = None
for line in open(f"{smoke}/GUROBI_LOG_SCRUBBED.txt", errors="ignore"):
    m = re.match(r"Barrier solved model in (\d+) iterations and ([\d.]+) seconds(?: \(([\d.]+) work units\))?", line)
    if m:
        it, sec, wu = int(m.group(1)), float(m.group(2)), (float(m.group(3)) if m.group(3) else None)
cpu = ""
try:
    cpu = next(l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name"))
except Exception:
    pass
json.dump(dict(run="S4M-2 s4m_A_integrated (local, 56x3h, profile A, 8 threads)", machine=cpu or platform.processor(), objective=rec.get("objective"), termination=rec.get("termination_condition"),
               barrier_iterations=it, barrier_seconds=sec, work_units=wu, seconds_per_work_unit=(sec / wu if (sec and wu) else None), seconds_per_iteration=(sec / it if (sec and it) else None),
               solve_seconds=rec.get("solve_seconds"), lp=rec.get("lp"), note="the probe network is the same LP (first 56 snapshots, representative weights); compare seconds per work unit (deterministic work measure) first"),
          open(ref_out, "w"), indent=1)
print("probe network and reference written")
PY
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
                                                              daily_network=r.get("daily_network"), build_seconds=r.get("build_seconds"), dust_cleanup=r.get("dust_cleanup"))
out = dict(commit=commit,
           note="every file listed under configs_and_research_inputs is inside code_<commit8>.tar.gz (git archive of the commit); the networks are pre-built (no rebuild on the instance); the NZE network carries the build override fuels.price_scenario=nze in its research_config; main settings: research.numerics.dust_cleanup on (decision 114), research.s2.industry.biomass_overflow_cap_share 0.98 (decision 115)",
           configs_and_research_inputs=files,
           renewable_profiles=dict(main_file="research_inputs/renewable_v5/profiles_calibrated_modern_c3_3h.nc", main_settings="profile_variant calibrated_modern, resource_classes 3 (decisions 74, 75)",
                                   manifest=prof, built_from_cutout=dict(file="cutouts/asean_zenodo_20325289/cutout-2013-era5.nc (NOT in the package)", bytes=7348721462,
                                   sha256="eaa033a328f39c82bbd4c46f74d72b19b7c7f2fcc1056e10b5cdf3a05f0d6f05", source_zip="work/p2_data_intake/raw11/bundle_cutouts_asean.zip",
                                   source_zip_sha256="028ae70154a9a84a696f96788fdf97ecde52ebc16a9c011cd30ebc3567f706df", doi="10.5281/zenodo.20325289", atlite=log.get("atlite"),
                                   cutout_shape=log.get("cutout_shape"))),
           network_builds=receipts, speed_probe=dict(network="networks/integrated_56_3h_probe_unsolved.nc", reference="PROBE_REFERENCE.json", script="speed_probe.sh", authorisation="separate user authorisation required"))
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
               main_settings=dict(dust_cleanup="on (decision 114; corrected rule, S4L-1)", biomass_overflow_cap_share="0.98 (decision 115)", solver_profile="formal_barrier (profile A; crossover profile abandoned, decision 114)"),
               run=dict(script="run_365x24h.sh", runs=["integrated (STEPS)", "disconnected (STEPS, extra-ASEAN CO2 storage on, CO2 shipping and Lao transit kept)",
                                                      "integrated_nze (NZE fuel prices)", "disconnected_gap (GAP_DIAGNOSTIC; only if the disconnected main ends non-optimal)"],
                        example="GRB_LICENSE_FILE=/path/to/gurobi.lic bash run_365x24h.sh --solver-profile formal_barrier --mode serial --auth '<user authorisation>'",
                        pilot="decision 116: first ONE integrated run (--runs integrated), then the batch; before the pilot the speed probe (speed_probe.sh, separate authorisation)",
                        modes=["serial (recommended)", "lanes2 (330 s licence gaps at start and inside a lane)"],
                        withdrawn_modes=["lanes3: the academic WLS licence allows at most 2 concurrent sessions, tokens kept >= 5 min (S4I K2, decision 106 a)"],
                        solver_profile="REQUIRED --solver-profile, no default; formal profile A: formal_barrier",
                        kirchhoff_row_normalisation="on (research.solver.scaling.kirchhoff_row_normalisation)", scaling="on",
                        exports_per_run=["SOLVE_RECEIPT.json", "V5_GATES.json (incl. B1_BUNKERS, B16_LEDGER)", "COUNTRY_COST_LEDGER.csv", "COUNTRY_COST_LEDGER_DETAIL.csv",
                                         "LEDGER_IDENTITY.json", "NODAL_PRICES.csv", "CO2_FLOWS.json", "BUNKER_ACCOUNT.json", "solved network", "MONITOR_<run>.csv (process-group RSS, cgroup memory)"],
                        threads_per_run=8, wall_clock_cap_s_default=15300, gurobi_time_limit_s_default=14400,
                        run_parameters="GUROBI_TIME_LIMIT_S / WALL_CAP_S / GRACE_S / MONITOR_S environment variables (S4M-3 point 2); scale after the speed probe",
                        kill_behaviour="setsid process group per solve, TERM then KILL after GRACE_S, export only after the group has exited, receipt version check (S4L-3)",
                        licence="GRB_LICENSE_FILE supplied by the user on the instance"),
               first_batch_runs=["integrated (STEPS) pilot first", "disconnected (STEPS)", "integrated_nze (NZE fuel prices)", "disconnected_gap (conditional)"],
               second_batch_sensitivities_registered_not_packaged=[
                   dict(name="extra-ASEAN CO2 storage price -50 % / +50 % (of 54.70 EUR2020/t)", override="co2.extra_asean_cost_scale=0.5 | 1.5", scenarios="integrated and disconnected"),
                   dict(name="unified ZEP 2011 storage cost 16.05 EUR/t for every geological storage (national, intra-ASEAN receivers, extra-ASEAN 40.75)",
                        override="s2.co2.sequestration_cost_eur_per_t=16.0535", scenarios="integrated and disconnected"),
                   dict(name="CO2 shipping distance: single route factor 1.091 instead of the pair-specific sea path", override="co2.ship_distance=route_factor", scenarios="integrated and disconnected"),
                   dict(name="Lao transit: nearest existing sea port and / or truck", override="co2.lao_transit_destination=existing_port ; co2.lao_transit_mode=truck", scenarios="integrated and disconnected"),
                   dict(name="LNG terminal expansion without cap, cost only (7,018 EUR/MW/a)", override="s3.gas.lng_expansion=uncapped_cost", scenarios="integrated and disconnected"),
                   dict(name="APG / AIMS plan caps per project group on top of the PyPSA-Eur limit (conservative, decision 96)", override="network.max_extension=apg_plans", scenarios="integrated and disconnected"),
                   dict(name="SG-VN and SG-KH DC candidates (APG other initiatives, decision 97 d)", override="corridors.optional_sg_vn_kh=on", scenarios="integrated"),
                   dict(name="author electrical parameters of the 19 readjusted cross-border AC lines and APG17 (decisions 98, 101 b comparison)", override="network.readjust_impedance=author", scenarios="integrated"),
                   dict(name="LA-VN grid stock of the author (1 MW split over lines 59 / 60 / 63 / 64; decision 100 comparison)", override="network.la_vn_stock=author", scenarios="integrated"),
                   dict(name="zero-capacity AC candidates with num_parallel 1.286 of template line 43 (former convention; decision 101 a comparison)", override="corridors.candidate_num_parallel=template43", scenarios="integrated"),
                   dict(name="non-industrial electricity as Astar residual (former method; decision 104 comparison)", override="demand.nonindustrial_electricity=astar_residual", scenarios="integrated and disconnected"),
                   dict(name="no transmission losses (S4H state; decision 105 a comparison)", override="network.transmission_losses=none", scenarios="integrated and disconnected"),
                   dict(name="AC loss proxy at the full allowed loading of one circuit (alpha 1.0; upper bound; decision 108)", override="network.ac_loss_reference_loading=1.0", scenarios="integrated and disconnected"),
                   dict(name="AC lines lossless, DC and pipeline losses kept (lower bound; decision 108)", override="network.ac_losses=none", scenarios="integrated and disconnected"),
                   dict(name="near-zero cleanup off (S4K / L23 state; decision 114 comparison)", override="numerics.dust_cleanup=off", scenarios="integrated and disconnected"),
                   dict(name="biomass overflow cap at the full potential (zero slack in BN / SG / VN; S4K / L23 state; decision 115 comparison)", override="s2.industry.biomass_overflow_cap_share=1.0", scenarios="integrated and disconnected")],
               supersedes="the S4K package (code 56d28358, L23 first batch) is void (S4M, decisions 114-116); the S4J (bcfb2d0a), S4H (6eead675), S4G (ed6af79c) and S4F (7e09744d) packages were voided earlier; S4L built networks but packaged nothing",
               coalition_run_rule="decision 95 f: a coalition run non-optimal with profile A is re-run once with profile C (barrier_numericfocus2); still non-optimal -> UNVERIFIED; coalition scope decided after delivery with item 14 (decision 97 f)"),
          open(os.path.join(dist, "PACKAGE_MANIFEST.json"), "w"), indent=1)
print("manifest written", len(rows), "files,", total, "bytes")
PY
du -sb "$DIST"; cat "$DIST/SHA256SUMS"
