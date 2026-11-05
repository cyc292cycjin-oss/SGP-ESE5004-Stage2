#!/bin/bash
# V3.1 HPC package builder (decision 195; V3_FIX_INSTRUCTION.md section 6; RUN_PLAN_HPC_V3.md section 15): the v3 package (hpc_v3/make_hpc_package_v3.sh) with the code of a
# new commit (bunker net-zero written per metering flow) and the v3.1 definition (run folders runs/batch5, runs/smoke56_v31); networks, env/, resources and limits are
# those of v3. New gate: the static zero-slack check (scripts_project/zero_slack_check.py, no solver) on the four package networks - any zero-slack forcing row, or a
# bunker hook not covering every metering flow, refuses the package. Files only (no HPC connection, no solve, no upload).
#   bash research/06_scope_redesign/p1_v3_20261102/hpc_v31/make_hpc_package_v31.sh <v3 package dir> <dist_dir>
# v3 package dir: work/p1_v3_20261102/hpc_package_v3 (its networks/ are copied after the check against the definition and its own SHA256SUMS)
# dist_dir:       new output folder (never overwritten), e.g. /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1
set -euo pipefail
V3=${1:?v3 package dir}; DIST=${2:?dist dir}
HV="$(cd "$(dirname "$0")" && pwd)"; D3="$(dirname "$HV")"; ROOT="$(cd "$D3/../../.." && pwd)"
HPR="$ROOT/research/06_scope_redesign/p1_hpr_20261027"; HPC="$HPR/hpc_package_src"
PKG4="$ROOT/research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4"; PKG3="$ROOT/research/06_scope_redesign/p1_m10p_20261022/cloud_package"
DEF="$D3/batch_def/BATCH_DEF_2920x3h_v31hpc.json"
PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}
cd "$ROOT"
COMMIT=$(git rev-parse HEAD); C8=${COMMIT:0:8}
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked changes not committed - commit first"; exit 1; }
[ ! -e "$DIST" ] || { echo "dist folder $DIST exists - choose a new one (never overwrite a package)"; exit 1; }
for f in "$DEF" "$D3/RUN_PLAN_HPC_V3.md" "$D3/HPC_OPERATOR_GUIDE_V3.md" "$D3/hpc_v3/REFERENCE_VALUES_V3.json" "$V3/SHA256SUMS"; do [ -s "$f" ] || { echo "missing $f"; exit 1; }; done
# V31_DRILL=1: a drill package for the local regression through the smoke job body (section 5.2) before section 15 exists - marked DRILL_ONLY_NOT_FOR_UPLOAD.txt,
# never placed under work/; the delivered package needs section 15 of RUN_PLAN_HPC_V3.md (committed before any v3.1 HPC solve)
DRILL=${V31_DRILL:-0}
case "$DIST" in */work/*) [ "$DRILL" = 0 ] || { echo "a drill package is never written under work/"; exit 1; };; esac
if [ "$DRILL" = 0 ]; then
  grep -q '^## 15\. v3\.1 修正' "$D3/RUN_PLAN_HPC_V3.md" || { echo "RUN_PLAN_HPC_V3.md has no section 15 (v3.1 fix) - write and commit it before packaging"; exit 1; }
fi
export BATCH_DEF="$DEF"
# 1. the four networks, their receipts and the cost table from the v3 package: each file against the v3 package's SHA256SUMS, the networks against the definition
NETFILES=(integrated_2920_3h_unsolved.nc no_new_xb_2920_3h_unsolved.nc integrated_ev05_2920_3h_unsolved.nc no_new_xb_ev05_2920_3h_unsolved.nc
          integrated_BUILD_RECEIPT.json integrated_ev05_BUILD_RECEIPT.json no_new_xb_2920_3h_VARIANT_RECEIPT.json no_new_xb_ev05_2920_3h_VARIANT_RECEIPT.json
          integrated_costs_active_research.csv)
( cd "$V3" && for f in "${NETFILES[@]}"; do grep -E "  networks/$f\$" SHA256SUMS; done | sha256sum -c --quiet ) || { echo "v3 package networks/ differ from its SHA256SUMS"; exit 1; }
eval "$("$PY" - "$DEF" <<'P'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("declare -A WANT=(" + " ".join(f"[{k}]={v}" for k, v in d["registered_sha"].items()) + ")")
print("declare -A BYTES=(" + " ".join(f"[{k}]={d['registered_bytes'][k]}" for k in d["registered_sha"]) + ")")
print("ZSC_ARGS=(" + " ".join(f"--network {rid}={r['scenario']}:NETS/{r['base']}_unsolved.nc" for rid, r in d["runs"].items()) + ")")
P
)"
[ "${#WANT[@]}" = 4 ] || { echo "the definition registers ${#WANT[@]} networks, not 4"; exit 1; }
for k in "${!WANT[@]}"; do
  [ "$(sha256sum "$V3/networks/$k" | cut -c1-64)" = "${WANT[$k]}" ] || { echo "$V3/networks/$k is not the registered network"; exit 1; }
  [ "$(stat -c %s "$V3/networks/$k")" = "${BYTES[$k]}" ] || { echo "$V3/networks/$k: byte count differs from the registered value"; exit 1; }
done
mkdir -p "$DIST/networks" "$DIST/env" "$DIST/hpc" "$DIST/pbs"
for f in "${NETFILES[@]}"; do cp "$V3/networks/$f" "$DIST/networks/$f"; done
"$PY" scripts_project/b4_batch4.py base-check --nets "$DIST/networks" --out "$DIST/networks/.base_check.json" > /dev/null || { cat "$DIST/networks/.base_check.json"; echo "base-check of the package networks failed"; exit 1; }
rm -f "$DIST/networks/.base_check.json"
# 2. V3.1 gate (V3_FIX_INSTRUCTION.md section 4): static zero-slack check of every hook row of the four networks (no solver) - not passed, no package
ZA=(); for x in "${ZSC_ARGS[@]}"; do ZA+=("${x//NETS/$DIST/networks}"); done
PYTHONHASHSEED=0 "$PY" scripts_project/zero_slack_check.py --repo "$ROOT" --out "$DIST/ZERO_SLACK_CHECK.json" "${ZA[@]}" > "$DIST/.zsc.log" 2>&1 \
  || { cat "$DIST/.zsc.log"; echo "REFUSED: zero-slack check not passed (ZERO_SLACK_CHECK.json) - no package"; exit 1; }
grep -q '^ZERO_SLACK_CHECK_RESULT:PASS$' "$DIST/.zsc.log" || { cat "$DIST/.zsc.log"; echo "REFUSED: zero-slack check result line missing"; exit 1; }
cat "$DIST/.zsc.log"; rm -f "$DIST/.zsc.log"
# 3. code: git archive of the commit without the top-level research/ folder
mapfile -t FILES < <(git ls-tree -r --name-only "$COMMIT" | grep -v '^research/')
git --literal-pathspecs archive --format=tar.gz -o "$DIST/code_${C8}.tar.gz" "$COMMIT" -- "${FILES[@]}"
[ "$(tar tzf "$DIST/code_${C8}.tar.gz" | grep -c '[^/]$')" = "${#FILES[@]}" ] || { echo "code archive: file count differs from the list"; exit 1; }
echo "$COMMIT" > "$DIST/COMMIT"
[ "$DRILL" = 0 ] || echo "DRILL package of commit $COMMIT for the local V3.1 regression (V3_FIX_INSTRUCTION.md 5.2) - not for upload" > "$DIST/DRILL_ONLY_NOT_FOR_UPLOAD.txt"
# 4. runner / preflight, pack, environment (third-batch lock), HPC scripts, definition, plans, guide, facts, reference values (as v3)
cp "$PKG4/run_batch4.sh" "$PKG4/preflight.sh" "$PKG3/pack_results.sh" "$DIST/"
cp "$PKG3/env/ENV_LOCK.txt" "$PKG3/env/conda_explicit_linux64.txt" "$PKG3/env/pip_only.txt" "$PKG3/env/ENV_DOWNLOAD.json" "$PKG3/env/install_env.sh" "$PKG3/env/env_check.py" "$DIST/env/"
cp "$HPC"/make_pbs.sh "$HPC"/hpr_job.sh "$HPC"/hpr_install_env.sh "$HPC"/hpr_preflight_login.sh "$HPC"/hpr_submit.sh "$HPC"/hpr_status.sh "$HPC"/hpr_consistency.py "$DIST/hpc/"
cp "$DEF" "$DIST/BATCH_DEF.json"
cp "$D3/RUN_PLAN_HPC_V3.md" "$D3/HPC_OPERATOR_GUIDE_V3.md" "$D3/V3_RULES.md" "$D3/RUN_PLAN_V3.md" "$HPR/HPC_FACTS_20261026.md" "$DIST/"
cp "$D3/hpc_v3/REFERENCE_VALUES_V3.json" "$DIST/REFERENCE_VALUES.json"
( cd "$DIST" && REPO="$ROOT" PY="$PY" bash hpc/make_pbs.sh pbs > pbs/MAKE_PBS.log )
grep -q '^RUNDIRS|runs/batch5|runs/smoke56_v31|' "$DIST/pbs/HPC_PLAN.txt" || { echo "pbs/HPC_PLAN.txt: run folders are not runs/batch5 / runs/smoke56_v31"; exit 1; }
chmod 755 "$DIST"/*.sh "$DIST/env/install_env.sh" "$DIST/hpc"/*.sh "$DIST/pbs"/*.pbs
# 5. consistency of the registered values (plan, definition / b4_batch4.py, runner, preflight, PBS scripts, job body, v3.1 run folders) - refused unless every row agrees
( cd "$DIST" && BATCH_DEF="$DIST/BATCH_DEF.json" "$PY" hpc/hpr_consistency.py --repo "$ROOT" --plan RUN_PLAN_HPC_V3.md --runner run_batch4.sh --preflight preflight.sh --pbs pbs --job hpc/hpr_job.sh --out HPC_CONSISTENCY.json > HPC_CONSISTENCY.txt ) \
  || { tail -40 "$DIST/HPC_CONSISTENCY.txt"; echo "REFUSED: registered values inconsistent (HPC_CONSISTENCY.txt)"; exit 1; }
( cd "$DIST" && find . -type f ! -name SHA256SUMS ! -name HPC_PACKAGE_MANIFEST.json -printf '%P\n' | LC_ALL=C sort | xargs sha256sum > SHA256SUMS )
# 6. refusals: licence-like content (patterns read at run time from a file OUTSIDE the repository, never written here), 365x24h files
PF=${LEAK_PATTERN_FILE:-$HOME/.dfx_leak_patterns}
if [ -r "$PF" ]; then
  pat=$(grep -v '^#' "$PF" | grep -E '^key=' | cut -d= -f2-)
  [ -z "$pat" ] || { grep -rIlE "$pat" "$DIST" > /dev/null 2>&1 && { echo "LICENCE-LIKE CONTENT IN THE PACKAGE - refused"; exit 1; } || echo "no licence-like content (pattern file $PF)"; }
else echo "NOTE: pattern file $PF not readable - the licence-like content check is left to the leak scan of the report step"; fi
ls "$DIST"/networks/*_365_24h_* > /dev/null 2>&1 && { echo "365x24h network in the package - refused"; exit 1; }
# 7. manifest
"$PY" - "$DIST" "$COMMIT" "$V3" "$C8" "$DRILL" <<'P'
import hashlib, json, os, sys, time
sys.path.insert(0, "scripts_project")
import b4_batch4 as B
dist, commit, v3, c8, drill = sys.argv[1:6]
rows = []
for line in open(os.path.join(dist, "SHA256SUMS")):
    s, p = line.split(maxsplit=1); p = p.strip(); rows.append(dict(path=p, bytes=os.path.getsize(os.path.join(dist, p)), sha256=s))
sums = os.path.join(dist, "SHA256SUMS"); total = sum(r["bytes"] for r in rows) + os.path.getsize(sums)
nets = {r["path"]: r["sha256"] for r in rows if r["path"].startswith("networks/") and r["path"].endswith(".nc")}
assert nets == {f"networks/{k}": v for k, v in B.REGISTERED_SHA.items()}, "network SHA256 differ from the registered values"
assert not any("365_24h" in p for p in nets), "a 365x24h network is in the package"
env = json.load(open(os.path.join(dist, "env", "ENV_DOWNLOAD.json")))
cons = json.load(open(os.path.join(dist, "HPC_CONSISTENCY.json")))
zsc = json.load(open(os.path.join(dist, "ZERO_SLACK_CHECK.json")))
assert zsc["passed"], "zero-slack check not passed"
h = lambda bps: round(total / bps / 3600, 2)
json.dump(dict(commit=commit, package=("DRILL (not for upload) " if drill != "0" else "") + "hpc_package_v3_1 (V3.1, decision 195: the v3 formal batch F1-F4 with the bunker net-zero written per metering flow; NUS Atlas PBS Pro, one job per run + batch job)",
               created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               files=rows, upload_total_bytes_excluding_this_manifest=total, sha256sums_sha256=hashlib.sha256(open(sums, "rb").read()).hexdigest(),
               upload=dict(method="ONE stream (scp -r of the folder) to /hpctmp/<user>/hpr31/ (a NEW folder; the v3 folder hpr3/ with its halted runs/batch4 stays untouched), then sha256sum -c SHA256SUMS on the login node; a failed file re-sent alone, then the full check again",
                           hours_at={"0.1 MB/s": h(1e5), "1 MB/s": h(1e6), "4 MB/s": h(4e6), "10 MB/s": h(10e6)}),
               code_archive=dict(file=f"code_{c8}.tar.gz", content=f"git archive of {commit} without the top-level research/ folder"),
               networks=dict(source=f"the v3 package {os.path.basename(v3)} (build {B.BUILD_COMMIT[:8]}), unchanged; registered in RUN_PLAN_V3.md section 24.1 and BATCH_DEF.json", files=nets, registered=B.REGISTERED_SHA, registered_bytes=B.REGISTERED_BYTES, no_365x24h=True),
               zero_slack_check=dict(file="ZERO_SLACK_CHECK.json", passed=zsc["passed"], rule=zsc["rule"], per_network={x["label"]: dict(passed=x["passed"], verdicts=x["verdicts"], bunker=x["bunker"].get("passed")) for x in zsc["networks"]}),
               environment=dict(lock="env/ENV_LOCK.txt", explicit="env/conda_explicit_linux64.txt", pip_only="env/pip_only.txt", reuse="the HPC environment already installed (HPR / v3 steps): preflight env section (env_check key packages identical) - no reinstall needed", check="env/env_check.py",
                                download_bytes=env["download_bytes"], conda_packages=env["conda_packages"], same_lock_as="third batch (M10P), packages v7-v9, V3 screening, v3 HPC package"),
               run=dict(plan="RUN_PLAN_HPC_V3.md (section 15: v3.1)", definition="BATCH_DEF.json", runner="run_batch4.sh (--only per job; POST_ONLY=1 batch job)", preflight=["preflight.sh (in-job, no licence section)", "hpc/hpr_preflight_login.sh"], pack="pack_results.sh",
                        run_dirs=B.RUN_DIRS, jobs=B.HPC_JOBS, pairs={p: list(v) for p, v in B.pairs().items()}, limits_status=B.LIMITS_STATUS, time_limit_s=B.TIME_LIMIT_S, wall_cap_s=B.WALL_CAP_S, licence_gap_s=B.LICENCE_GAP_S,
                        wait_start_max_s=B.WAIT_START_MAX_S, build_timeout_s=B.BUILD_TIMEOUT_S, smoke=B.SMOKE, smoke_expected_objective=B.SMOKE_EXPECTED_OBJECTIVE,
                        thresholds=dict(memory_stop_fraction=B.MEMORY_STOP_FRACTION, projection_fraction=B.PROJECTION_FRACTION, iterations_reference={k: v["iterations_reference"] for k, v in B.RUNS.items()}),
                        solve_mode="split (process 1 s2_solve.py --split-stage build, process 2 b4_split_solve.py, process 3 s2_solve.py --split-stage assign)",
                        licence="GRB_LICENSE_FILE=$HOME/.gurobi/gurobi.lic placed by the user; never in the package; referenced only by the jobs"),
               consistency=dict(file="HPC_CONSISTENCY.json", all_consistent=cons["all_consistent"], rows=len(cons["rows"])),
               operator_guide="HPC_OPERATOR_GUIDE_V3.md (v3.1)", facts="HPC_FACTS_20261026.md", reference_values="REFERENCE_VALUES.json (numbers only: v3 365x24h rerun / first screening V1 / V2, local 56-snapshot smokes S-A / S-B)",
               local_smoke="RUN_PLAN_V3.md section 25 (expected HPC smoke values, unchanged) and RUN_PLAN_HPC_V3.md section 15 (v3.1 local 56-snapshot regression through the smoke job body)",
               never_included=["licence", "cutout", "LP / solution arrays", "365x24h networks", "results", "account / host / connection information"]),
          open(os.path.join(dist, "HPC_PACKAGE_MANIFEST.json"), "w"), indent=1)
print("manifest:", len(rows), "files,", total, "bytes; limits", B.LIMITS_STATUS, "; run dirs", B.RUN_DIRS)
P
du -sb "$DIST"
