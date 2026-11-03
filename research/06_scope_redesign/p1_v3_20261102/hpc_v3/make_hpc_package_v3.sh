#!/bin/bash
# V3 HPC package builder (instruction V14 section 6.1; RUN_PLAN_HPC_V3.md): assemble the HPC deployment package of the v3 formal batch (F1-F4 on the 2920x3h
# networks of the build a1ef782b, NUS Atlas PBS Pro, one job per run + one batch job) in WSL from the repository root of the branch with a clean tracked tree;
# files only (no HPC connection, no solve, no upload).
#   bash research/06_scope_redesign/p1_v3_20261102/hpc_v3/make_hpc_package_v3.sh <builds_dir> <dist_dir>
# builds_dir: results_project/v3hpc/builds of the main checkout (sa/ = F1 / F2, sa_ev05/ = F3 / F4; RUN_PLAN_V3.md section 24.1)
# dist_dir:   new output folder (never overwritten), e.g. /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3
# Writes: code_<commit8>.tar.gz (git archive of HEAD without the top-level research/ folder), BATCH_DEF.json (batch_def/BATCH_DEF_2920x3h_v3hpc.json), networks/ (the four
# 2920x3h networks under their package names, their build / variant receipts, the shared cost table; NO 365x24h file), run_batch4.sh + preflight.sh (B4P sources with the
# HPR and V3 HPC amendments), pack_results.sh + env/ (third batch, unchanged), hpc/ (job body, PBS generator, install, login preflight, submit, status, consistency),
# pbs/ (generated from b4_batch4.py hpc-plan with the definition), RUN_PLAN_HPC_V3.md, HPC_OPERATOR_GUIDE_V3.md, HPC_FACTS_20261026.md, REFERENCE_VALUES.json (values only),
# V3_RULES.md, RUN_PLAN_V3.md, HPC_CONSISTENCY.json, COMMIT, SHA256SUMS, HPC_PACKAGE_MANIFEST.json. Never the licence, the cutout, LP / solution arrays, results,
# 365x24h networks, account or host information.
set -euo pipefail
B=${1:?builds dir}; DIST=${2:?dist dir}
HV="$(cd "$(dirname "$0")" && pwd)"; D3="$(dirname "$HV")"; ROOT="$(cd "$D3/../../.." && pwd)"
HPR="$ROOT/research/06_scope_redesign/p1_hpr_20261027"; HPC="$HPR/hpc_package_src"
PKG4="$ROOT/research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4"; PKG3="$ROOT/research/06_scope_redesign/p1_m10p_20261022/cloud_package"
DEF="$D3/batch_def/BATCH_DEF_2920x3h_v3hpc.json"
PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}
cd "$ROOT"
COMMIT=$(git rev-parse HEAD); C8=${COMMIT:0:8}
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked changes not committed - commit first"; exit 1; }
[ ! -e "$DIST" ] || { echo "dist folder $DIST exists - choose a new one (never overwrite a package)"; exit 1; }
for f in "$DEF" "$D3/RUN_PLAN_HPC_V3.md" "$D3/HPC_OPERATOR_GUIDE_V3.md" "$HV/REFERENCE_VALUES_V3.json"; do [ -s "$f" ] || { echo "missing $f"; exit 1; }; done
export BATCH_DEF="$DEF"
# 1. the four networks (package name <- build file), their receipts, the cost table; every file checked against the definition before copying
declare -A SRC=([integrated_2920_3h]="$B/sa/integrated/integrated_2920_3h_unsolved.nc" [no_new_xb_2920_3h]="$B/sa/no_new_xb/no_new_xb_2920_3h_unsolved.nc"
                [integrated_ev05_2920_3h]="$B/sa_ev05/integrated/integrated_2920_3h_unsolved.nc" [no_new_xb_ev05_2920_3h]="$B/sa_ev05/no_new_xb/no_new_xb_2920_3h_unsolved.nc")
declare -A REC=([integrated_BUILD_RECEIPT.json]="$B/sa/integrated/integrated_BUILD_RECEIPT.json" [integrated_ev05_BUILD_RECEIPT.json]="$B/sa_ev05/integrated/integrated_BUILD_RECEIPT.json"
                [no_new_xb_2920_3h_VARIANT_RECEIPT.json]="$B/sa/no_new_xb/no_new_xb_2920_3h_VARIANT_RECEIPT.json" [no_new_xb_ev05_2920_3h_VARIANT_RECEIPT.json]="$B/sa_ev05/no_new_xb/no_new_xb_2920_3h_VARIANT_RECEIPT.json")
eval "$("$PY" - "$DEF" <<'P'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("declare -A WANT=(" + " ".join(f"[{k[:-len('_unsolved.nc')]}]={v}" for k, v in d["registered_sha"].items()) + ")")
print("declare -A BYTES=(" + " ".join(f"[{k[:-len('_unsolved.nc')]}]={d['registered_bytes'][k]}" for k in d["registered_sha"]) + ")")
print(f"BUILD_COMMIT={d['build_commit']}")
P
)"
[ "${#WANT[@]}" = 4 ] || { echo "the definition registers ${#WANT[@]} networks, not 4"; exit 1; }
for k in "${!SRC[@]}"; do
  f=${SRC[$k]}
  [ "$(sha256sum "$f" | cut -c1-64)" = "${WANT[$k]}" ] || { echo "$f is not the registered $k"; exit 1; }
  [ "$(stat -c %s "$f")" = "${BYTES[$k]}" ] || { echo "$f: byte count differs from the registered value"; exit 1; }
done
cmp -s "$B/sa/integrated/costs_active_research.csv" "$B/sa_ev05/integrated/costs_active_research.csv" || { echo "the cost tables of the two builds differ - the four runs share one table"; exit 1; }
mkdir -p "$DIST/networks" "$DIST/env" "$DIST/hpc" "$DIST/pbs"
for k in "${!SRC[@]}"; do cp "${SRC[$k]}" "$DIST/networks/${k}_unsolved.nc"; done
for k in "${!REC[@]}"; do cp "${REC[$k]}" "$DIST/networks/$k"; done
cp "$B/sa/integrated/costs_active_research.csv" "$DIST/networks/integrated_costs_active_research.csv"
# the receipt chain and the registered values with the package's own check (b4_batch4.py base-check = the preflight networks section)
"$PY" scripts_project/b4_batch4.py base-check --nets "$DIST/networks" --out "$DIST/networks/.base_check.json" > /dev/null || { cat "$DIST/networks/.base_check.json"; echo "base-check of the package networks failed"; exit 1; }
rm -f "$DIST/networks/.base_check.json"
# 2. code: git archive of the commit without the top-level research/ folder
mapfile -t FILES < <(git ls-tree -r --name-only "$COMMIT" | grep -v '^research/')
git --literal-pathspecs archive --format=tar.gz -o "$DIST/code_${C8}.tar.gz" "$COMMIT" -- "${FILES[@]}"
[ "$(tar tzf "$DIST/code_${C8}.tar.gz" | grep -c '[^/]$')" = "${#FILES[@]}" ] || { echo "code archive: file count differs from the list"; exit 1; }
echo "$COMMIT" > "$DIST/COMMIT"
# 3. runner / preflight, pack, environment (third-batch lock), HPC scripts, definition, plans, guide, facts, reference values
cp "$PKG4/run_batch4.sh" "$PKG4/preflight.sh" "$PKG3/pack_results.sh" "$DIST/"
cp "$PKG3/env/ENV_LOCK.txt" "$PKG3/env/conda_explicit_linux64.txt" "$PKG3/env/pip_only.txt" "$PKG3/env/ENV_DOWNLOAD.json" "$PKG3/env/install_env.sh" "$PKG3/env/env_check.py" "$DIST/env/"
cp "$HPC"/make_pbs.sh "$HPC"/hpr_job.sh "$HPC"/hpr_install_env.sh "$HPC"/hpr_preflight_login.sh "$HPC"/hpr_submit.sh "$HPC"/hpr_status.sh "$HPC"/hpr_consistency.py "$DIST/hpc/"
cp "$DEF" "$DIST/BATCH_DEF.json"
cp "$D3/RUN_PLAN_HPC_V3.md" "$D3/HPC_OPERATOR_GUIDE_V3.md" "$D3/V3_RULES.md" "$D3/RUN_PLAN_V3.md" "$HPR/HPC_FACTS_20261026.md" "$DIST/"
cp "$HV/REFERENCE_VALUES_V3.json" "$DIST/REFERENCE_VALUES.json"
( cd "$DIST" && REPO="$ROOT" PY="$PY" bash hpc/make_pbs.sh pbs > pbs/MAKE_PBS.log )
chmod 755 "$DIST"/*.sh "$DIST/env/install_env.sh" "$DIST/hpc"/*.sh "$DIST/pbs"/*.pbs
# 4. consistency of the registered values (plan, definition / b4_batch4.py, runner, preflight, PBS scripts, job body) - refused unless every row agrees
( cd "$DIST" && BATCH_DEF="$DIST/BATCH_DEF.json" "$PY" hpc/hpr_consistency.py --repo "$ROOT" --plan RUN_PLAN_HPC_V3.md --runner run_batch4.sh --preflight preflight.sh --pbs pbs --job hpc/hpr_job.sh --out HPC_CONSISTENCY.json > HPC_CONSISTENCY.txt ) \
  || { tail -40 "$DIST/HPC_CONSISTENCY.txt"; echo "REFUSED: registered values inconsistent (HPC_CONSISTENCY.txt)"; exit 1; }
( cd "$DIST" && find . -type f ! -name SHA256SUMS ! -name HPC_PACKAGE_MANIFEST.json -printf '%P\n' | LC_ALL=C sort | xargs sha256sum > SHA256SUMS )
# 5. refusals: licence-like content (patterns read at run time from a file OUTSIDE the repository, never written here), 365x24h files
PF=${LEAK_PATTERN_FILE:-$HOME/.dfx_leak_patterns}
if [ -r "$PF" ]; then
  pat=$(grep -v '^#' "$PF" | grep -E '^key=' | cut -d= -f2-)
  [ -z "$pat" ] || { grep -rIlE "$pat" "$DIST" > /dev/null 2>&1 && { echo "LICENCE-LIKE CONTENT IN THE PACKAGE - refused"; exit 1; } || echo "no licence-like content (pattern file $PF)"; }
else echo "NOTE: pattern file $PF not readable - the licence-like content check is left to the leak scan of the report step"; fi
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
cons = json.load(open(os.path.join(dist, "HPC_CONSISTENCY.json")))
h = lambda bps: round(total / bps / 3600, 2)
json.dump(dict(commit=commit, package="hpc_package_v3 (V3 formal batch F1-F4: S-A shipping, EV fleet x0.5 pair; NUS Atlas PBS Pro, one job per run + batch job)", created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               files=rows, upload_total_bytes_excluding_this_manifest=total, sha256sums_sha256=hashlib.sha256(open(sums, "rb").read()).hexdigest(),
               upload=dict(method="ONE stream (scp -r of the folder or one rsync) to /hpctmp/<user>/hpr3/, then sha256sum -c SHA256SUMS on the login node; a failed file re-sent alone, then the full check again", hours_at={"0.1 MB/s": h(1e5), "1 MB/s": h(1e6), "4 MB/s": h(4e6), "10 MB/s": h(10e6)}),
               code_archive=dict(file=f"code_{c8}.tar.gz", content=f"git archive of {commit} without the top-level research/ folder"),
               networks=dict(source=f"V3 HPC builds, commit {B.BUILD_COMMIT[:8]} (main checkout results_project/v3hpc/{os.path.basename(b)}); registered in RUN_PLAN_V3.md section 24.1 and BATCH_DEF.json", files=nets, registered=B.REGISTERED_SHA, registered_bytes=B.REGISTERED_BYTES, no_365x24h=True),
               environment=dict(lock="env/ENV_LOCK.txt", explicit="env/conda_explicit_linux64.txt", pip_only="env/pip_only.txt", reuse="the HPC environment of the HPR steps: preflight env section (env_check key packages identical) - no reinstall needed", check="env/env_check.py",
                                download_bytes=env["download_bytes"], conda_packages=env["conda_packages"], same_lock_as="third batch (M10P), packages v7-v9, V3 screening"),
               run=dict(plan="RUN_PLAN_HPC_V3.md", definition="BATCH_DEF.json", runner="run_batch4.sh (--only per job; POST_ONLY=1 batch job)", preflight=["preflight.sh (in-job, no licence section)", "hpc/hpr_preflight_login.sh"], pack="pack_results.sh",
                        jobs=B.HPC_JOBS, pairs={p: list(v) for p, v in B.pairs().items()}, limits_status=B.LIMITS_STATUS, time_limit_s=B.TIME_LIMIT_S, wall_cap_s=B.WALL_CAP_S, licence_gap_s=B.LICENCE_GAP_S,
                        wait_start_max_s=B.WAIT_START_MAX_S, build_timeout_s=B.BUILD_TIMEOUT_S, smoke=B.SMOKE, smoke_expected_objective=B.SMOKE_EXPECTED_OBJECTIVE,
                        thresholds=dict(memory_stop_fraction=B.MEMORY_STOP_FRACTION, projection_fraction=B.PROJECTION_FRACTION, iterations_reference={k: v["iterations_reference"] for k, v in B.RUNS.items()}),
                        solve_mode="split (process 1 s2_solve.py --split-stage build, process 2 b4_split_solve.py, process 3 s2_solve.py --split-stage assign)",
                        licence="GRB_LICENSE_FILE=$HOME/.gurobi/gurobi.lic placed by the user; never in the package; referenced only by the jobs"),
               consistency=dict(file="HPC_CONSISTENCY.json", all_consistent=cons["all_consistent"], rows=len(cons["rows"])),
               operator_guide="HPC_OPERATOR_GUIDE_V3.md", facts="HPC_FACTS_20261026.md", reference_values="REFERENCE_VALUES.json (numbers only: v3 365x24h rerun / first screening V1 / V2, local 56-snapshot smokes S-A / S-B)",
               local_smoke="RUN_PLAN_V3.md section 24.2: two local Gurobi calls on the first 56 snapshots of F1 / F2 (single-process s2_solve path, = supplements 01-05); their objectives are the expected HPC smoke values (BATCH_DEF.json smoke_expected)",
               never_included=["licence", "cutout", "LP / solution arrays", "365x24h networks", "results", "account / host / connection information"]),
          open(os.path.join(dist, "HPC_PACKAGE_MANIFEST.json"), "w"), indent=1)
print("manifest:", len(rows), "files,", total, "bytes; limits", B.LIMITS_STATUS)
P
du -sb "$DIST"
