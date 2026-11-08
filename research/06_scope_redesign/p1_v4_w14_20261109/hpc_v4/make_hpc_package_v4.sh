#!/bin/bash
# V4 W14 HPC package builder (V4_W14_INSTRUCTION.md section 3.1; RUN_PLAN_HPC_V4.md): the v3.1 package layout (p1_v3_20261102/hpc_v31/make_hpc_package_v31.sh) with
#   - the two v4 main 2920x3h networks of the W14 build (results_project/v4w14/builds/main; build commit and SHA256 / bytes registered in batch_def/BATCH_DEF_2920x3h_v4hpc.json),
#     their build / variant receipts and the integrated cost table;
#   - the code of the CURRENT commit (= the package COMMIT, the last commit of the branch before packaging) without the top-level research/ folder;
#   - the runner and status command of D1 (p1_v4_d1_20261107/hpc_v4/run_batch4.sh, hpr_status.sh: the package COMMIT into RUN.json and the solve receipt; both
#     objective values), the v4 preflight (hpc_v4/preflight.sh: + the D1 switch-set / network-metadata check), the HPR job scripts (job names hpr4_* from the definition),
#     the environment of the third batch (same lock file as v3.1), pack_results.sh, the v4 definition, plan, operator guide, facts and reference values.
# Gates (no package otherwise): network SHA256 / bytes = definition; base-check (receipts, build commit); the V3.1 zero-slack check; the consistency of the registered
# values (plan / definition / runner / preflight / PBS scripts / job body); the licence-like string scan of pack_results.sh over the whole package and the unpacked code;
# no 365x24h network; and the package's own preflight (guards, sha, networks incl. the v4 metadata check, env, profile, code, tools) on a copy of it.
# Files only: no HPC connection, no solve, no upload.
#   bash research/06_scope_redesign/p1_v4_w14_20261109/hpc_v4/make_hpc_package_v4.sh <dist_dir>
# dist_dir: new output folder (never overwritten), e.g. /mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w14_20261109/hpc_package_v4
# W14_DRILL=1: a drill package outside work/ (marked DRILL_ONLY_NOT_FOR_UPLOAD.txt) for testing the builder before the registration commit.
set -euo pipefail
DIST=${1:?dist dir}
HV="$(cd "$(dirname "$0")" && pwd)"; D4="$(dirname "$HV")"; ROOT="$(cd "$D4/../../.." && pwd)"
HPR="$ROOT/research/06_scope_redesign/p1_hpr_20261027"; HPC="$HPR/hpc_package_src"; D1="$ROOT/research/06_scope_redesign/p1_v4_d1_20261107/hpc_v4"
PKG3="$ROOT/research/06_scope_redesign/p1_m10p_20261022/cloud_package"
DEF="$D4/batch_def/BATCH_DEF_2920x3h_v4hpc.json"
MAIN=${MAIN:-/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model}; NSRC=${NETS_SRC:-$MAIN/results_project/v4w14/builds/main}
PY=${PY:-$HOME/miniforge3/envs/pypsa-earth/bin/python}
export PYTHONHASHSEED=0 PROJ_DATA=${PROJ_DATA:-$HOME/miniforge3/envs/pypsa-earth/share/proj} PROJ_LIB=${PROJ_LIB:-$HOME/miniforge3/envs/pypsa-earth/share/proj}
cd "$ROOT"
COMMIT=$(git rev-parse HEAD); C8=${COMMIT:0:8}
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked changes not committed - commit first"; exit 1; }
[ ! -e "$DIST" ] || { echo "dist folder $DIST exists - choose a new one (never overwrite a package)"; exit 1; }
DRILL=${W14_DRILL:-0}
case "$DIST" in */work/*) [ "$DRILL" = 0 ] || { echo "a drill package is never written under work/"; exit 1; };; esac
for f in "$DEF" "$D4/RUN_PLAN_HPC_V4.md" "$D4/HPC_OPERATOR_GUIDE_V4.md" "$HV/REFERENCE_VALUES_V4.json" "$HV/preflight.sh" "$D1/run_batch4.sh" "$D1/hpr_status.sh"; do [ -s "$f" ] || { echo "missing $f"; exit 1; }; done
if [ "$DRILL" = 0 ]; then
  grep -q '登记状态 | \*\*REGISTERED\*\*' "$D4/RUN_PLAN_HPC_V4.md" || { echo "RUN_PLAN_HPC_V4.md is not the registered plan - write and commit it before packaging"; exit 1; }
fi
"$PY" -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get('limits_status') == 'REGISTERED' else 1)" "$DEF" || { echo "definition not REGISTERED"; exit 1; }
export BATCH_DEF="$DEF"
# 1. the two networks, their receipts and the cost table from the W14 build: SHA256 / bytes against the definition, build commit of the receipt
declare -A SRC=([integrated_2920_3h_unsolved.nc]=integrated/integrated_2920_3h_unsolved.nc [no_new_xb_2920_3h_unsolved.nc]=no_new_xb/no_new_xb_2920_3h_unsolved.nc
                [integrated_BUILD_RECEIPT.json]=integrated/integrated_BUILD_RECEIPT.json [no_new_xb_2920_3h_VARIANT_RECEIPT.json]=no_new_xb/no_new_xb_2920_3h_VARIANT_RECEIPT.json
                [integrated_costs_active_research.csv]=integrated/costs_active_research.csv)
eval "$("$PY" - "$DEF" <<'P'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("declare -A WANT=(" + " ".join(f"[{k}]={v}" for k, v in d["registered_sha"].items()) + ")")
print("declare -A BYTES=(" + " ".join(f"[{k}]={d['registered_bytes'][k]}" for k in d["registered_sha"]) + ")")
print("ZSC_ARGS=(" + " ".join(f"--network {rid}={r['scenario']}:NETS/{r['base']}_unsolved.nc" for rid, r in d["runs"].items()) + ")")
print("BUILD_COMMIT=" + d["build_commit"])
P
)"
[ "${#WANT[@]}" = 2 ] || { echo "the definition registers ${#WANT[@]} networks, not 2"; exit 1; }
mkdir -p "$DIST/networks" "$DIST/env" "$DIST/hpc" "$DIST/pbs"
for k in "${!SRC[@]}"; do cp "$NSRC/${SRC[$k]}" "$DIST/networks/$k"; done
for k in "${!WANT[@]}"; do
  [ "$(sha256sum "$DIST/networks/$k" | cut -c1-64)" = "${WANT[$k]}" ] || { echo "$k is not the registered network"; exit 1; }
  [ "$(stat -c %s "$DIST/networks/$k")" = "${BYTES[$k]}" ] || { echo "$k: byte count differs from the registered value"; exit 1; }
done
"$PY" -c "import json,sys; r=json.load(open(sys.argv[1])); sys.exit(0 if r.get('code_sha') == sys.argv[2] else 1)" "$DIST/networks/integrated_BUILD_RECEIPT.json" "$BUILD_COMMIT" || { echo "build receipt code_sha is not the registered build commit"; exit 1; }
echo "code outside research/ differs from the build commit ${BUILD_COMMIT:0:8}: $(git diff --name-only "$BUILD_COMMIT" "$COMMIT" -- . ':!research/' | wc -l) file(s)"
[ "$(git diff --name-only "$BUILD_COMMIT" "$COMMIT" -- . ':!research/' | wc -l)" = 0 ] || { echo "REFUSED: the package code differs from the build commit outside research/"; exit 1; }
"$PY" scripts_project/b4_batch4.py base-check --nets "$DIST/networks" --out "$DIST/networks/.base_check.json" > /dev/null || { cat "$DIST/networks/.base_check.json"; echo "base-check of the package networks failed"; exit 1; }
rm -f "$DIST/networks/.base_check.json"
# 2. V3.1 gate: static zero-slack check of every hook row of the two networks (no solver) - not passed, no package
ZA=(); for x in "${ZSC_ARGS[@]}"; do ZA+=("${x//NETS/$DIST/networks}"); done
"$PY" scripts_project/zero_slack_check.py --repo "$ROOT" --out "$DIST/ZERO_SLACK_CHECK.json" "${ZA[@]}" > "$DIST/.zsc.log" 2>&1 \
  || { cat "$DIST/.zsc.log"; echo "REFUSED: zero-slack check not passed (ZERO_SLACK_CHECK.json) - no package"; exit 1; }
grep -q '^ZERO_SLACK_CHECK_RESULT:PASS$' "$DIST/.zsc.log" || { cat "$DIST/.zsc.log"; echo "REFUSED: zero-slack check result line missing"; exit 1; }
grep -E '^ZERO_SLACK' "$DIST/.zsc.log"; rm -f "$DIST/.zsc.log"
# 3. code: git archive of the commit without the top-level research/ folder
mapfile -t FILES < <(git ls-tree -r --name-only "$COMMIT" | grep -v '^research/')
git --literal-pathspecs archive --format=tar.gz -o "$DIST/code_${C8}.tar.gz" "$COMMIT" -- "${FILES[@]}"
[ "$(tar tzf "$DIST/code_${C8}.tar.gz" | grep -c '[^/]$')" = "${#FILES[@]}" ] || { echo "code archive: file count differs from the list"; exit 1; }
echo "$COMMIT" > "$DIST/COMMIT"
[ "$DRILL" = 0 ] || echo "DRILL package of commit $COMMIT for testing the W14 builder - not for upload" > "$DIST/DRILL_ONLY_NOT_FOR_UPLOAD.txt"
# 4. runner / preflight / pack, environment (third-batch lock = v3.1), HPC scripts, definition, plan, guide, facts, reference values
cp "$D1/run_batch4.sh" "$HV/preflight.sh" "$PKG3/pack_results.sh" "$DIST/"
cp "$PKG3/env/ENV_LOCK.txt" "$PKG3/env/conda_explicit_linux64.txt" "$PKG3/env/pip_only.txt" "$PKG3/env/ENV_DOWNLOAD.json" "$PKG3/env/install_env.sh" "$PKG3/env/env_check.py" "$DIST/env/"
cp "$HPC"/make_pbs.sh "$HPC"/hpr_job.sh "$HPC"/hpr_install_env.sh "$HPC"/hpr_preflight_login.sh "$HPC"/hpr_submit.sh "$HPC"/hpr_consistency.py "$DIST/hpc/"
cp "$D1/hpr_status.sh" "$DIST/hpc/hpr_status.sh"
cp "$DEF" "$DIST/BATCH_DEF.json"
cp "$D4/RUN_PLAN_HPC_V4.md" "$D4/HPC_OPERATOR_GUIDE_V4.md" "$HPR/HPC_FACTS_20261026.md" "$DIST/"
cp "$HV/REFERENCE_VALUES_V4.json" "$DIST/REFERENCE_VALUES.json"
( cd "$DIST" && REPO="$ROOT" PY="$PY" bash hpc/make_pbs.sh pbs > pbs/MAKE_PBS.log )
grep -q '^RUNDIRS|runs/batch6|runs/smoke56_v4|' "$DIST/pbs/HPC_PLAN.txt" || { echo "pbs/HPC_PLAN.txt: run folders are not runs/batch6 / runs/smoke56_v4"; exit 1; }
[ "$(ls "$DIST"/pbs/hpr4_*.pbs | wc -l)" = 6 ] && [ -z "$(ls "$DIST"/pbs/*.pbs | grep -v '/hpr4_')" ] || { echo "pbs/: the six job scripts must all be hpr4_*"; exit 1; }
chmod 755 "$DIST"/*.sh "$DIST/env/install_env.sh" "$DIST/hpc"/*.sh "$DIST/pbs"/*.pbs
# 5. consistency of the registered values (plan, definition / b4_batch4.py, runner, preflight, PBS scripts, job body, run folders) - refused unless every row agrees
( cd "$DIST" && BATCH_DEF="$DIST/BATCH_DEF.json" "$PY" hpc/hpr_consistency.py --repo "$ROOT" --plan RUN_PLAN_HPC_V4.md --runner run_batch4.sh --preflight preflight.sh --pbs pbs --job hpc/hpr_job.sh --out HPC_CONSISTENCY.json > HPC_CONSISTENCY.txt ) \
  || { tail -40 "$DIST/HPC_CONSISTENCY.txt"; echo "REFUSED: registered values inconsistent (HPC_CONSISTENCY.txt)"; exit 1; }
tail -1 "$DIST/HPC_CONSISTENCY.txt"
( cd "$DIST" && find . -type f ! -name SHA256SUMS ! -name HPC_PACKAGE_MANIFEST.json -printf '%P\n' | LC_ALL=C sort | xargs sha256sum > SHA256SUMS )
# 6. refusals: licence-like strings (the regex of pack_results.sh, case-insensitive, text files) in the package; 365x24h networks
LRX='license[i]d|registered[[:space:]]+to|wls(secret|accessid)'
if grep -rIilE "$LRX" "$DIST" > /dev/null 2>&1; then grep -rIilE "$LRX" "$DIST" | head -5; echo "LICENCE-LIKE STRING IN THE PACKAGE (pack_results.sh regex) - refused"; exit 1; fi
echo "licence-like strings (pack_results.sh regex) in the package: 0 files"
PF=${LEAK_PATTERN_FILE:-$HOME/.dfx_leak_patterns}
if [ -r "$PF" ]; then
  pat=$(grep -v '^#' "$PF" | grep -E '^key=' | cut -d= -f2-)
  [ -z "$pat" ] || { grep -rIlE "$pat" "$DIST" > /dev/null 2>&1 && { echo "LICENCE-LIKE CONTENT IN THE PACKAGE (pattern file) - refused"; exit 1; } || echo "no licence-like content (pattern file)"; }
fi
ls "$DIST"/networks/*_365_24h_* > /dev/null 2>&1 && { echo "365x24h network in the package - refused"; exit 1; }
# 7. the package's own preflight on a copy (the code unpacked to ./repo there): guards, sha, networks (base-check + v4 metadata), env, profile, code, tools;
#    and the licence-like string scan of the unpacked code
CHK=$(mktemp -d "${TMPDIR:-/tmp}/w14_pkgcheck_XXXXXX"); cp -r "$DIST" "$CHK/pkg"
( cd "$CHK/pkg" && env -u GRB_LICENSE_FILE PY="$PY" PREFLIGHT_ONLY=guards,sha,networks,env,profile,code,tools bash preflight.sh > "$CHK/preflight.txt" 2>&1 ) || { tail -30 "$CHK/preflight.txt"; echo "REFUSED: the package preflight failed on a copy ($CHK)"; exit 1; }
grep -E "files OK|limits of the package|v4 network metadata|^F[12] |PREFLIGHT OK" "$CHK/preflight.txt" || true
if grep -rIilE "$LRX" "$CHK/pkg/repo" > /dev/null 2>&1; then grep -rIilE "$LRX" "$CHK/pkg/repo" | head -5; echo "LICENCE-LIKE STRING IN THE UNPACKED CODE - refused"; exit 1; fi
echo "licence-like strings (pack_results.sh regex) in the unpacked code: 0 files"
cp "$CHK/preflight.txt" "${DIST}_preflight_check.txt"   # next to the package folder (not inside it; never uploaded)
rm -rf "$CHK"
# 8. manifest
"$PY" - "$DIST" "$COMMIT" "$C8" "$DRILL" <<'P'
import hashlib, json, os, sys, time
sys.path.insert(0, "scripts_project")
import b4_batch4 as B
dist, commit, c8, drill = sys.argv[1:5]
rows = []
for line in open(os.path.join(dist, "SHA256SUMS")):
    s, p = line.split(maxsplit=1); p = p.strip(); rows.append(dict(path=p, bytes=os.path.getsize(os.path.join(dist, p)), sha256=s))
sums = os.path.join(dist, "SHA256SUMS"); total = sum(r["bytes"] for r in rows) + os.path.getsize(sums)
nets = {r["path"]: r["sha256"] for r in rows if r["path"].startswith("networks/") and r["path"].endswith(".nc")}
assert nets == {f"networks/{k}": v for k, v in B.REGISTERED_SHA.items()}, "network SHA256 differ from the registered values"
env = json.load(open(os.path.join(dist, "env", "ENV_DOWNLOAD.json")))
cons = json.load(open(os.path.join(dist, "HPC_CONSISTENCY.json")))
zsc = json.load(open(os.path.join(dist, "ZERO_SLACK_CHECK.json")))
d = json.load(open(os.path.join(dist, "BATCH_DEF.json")))
assert zsc["passed"], "zero-slack check not passed"
h = lambda bps: round(total / bps / 3600, 2)
json.dump(dict(commit=commit, package=("DRILL (not for upload) " if drill != "0" else "") + "hpc_package_v4 (V4 W14, decision 222: the v4 main pair F1 integrated / F2 no_new_xb + batch job; NUS Atlas PBS Pro, one job per run + batch job)",
               created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               files=rows, upload_total_bytes_excluding_this_manifest=total, sha256sums_sha256=hashlib.sha256(open(sums, "rb").read()).hexdigest(),
               upload=dict(method="ONE stream (scp -r of the folder) to /hpctmp/<user>/hpr4/ (a NEW folder; the v3 / v3.1 folders hpr3/, hpr31/ stay untouched), then sha256sum -c SHA256SUMS on the login node; a failed file re-sent alone, then the full check again",
                           hours_at={"0.1 MB/s": h(1e5), "1 MB/s": h(1e6), "4 MB/s": h(4e6), "10 MB/s": h(10e6)}),
               code_archive=dict(file=f"code_{c8}.tar.gz", content=f"git archive of {commit} without the top-level research/ folder; identical outside research/ to the network build commit {B.BUILD_COMMIT}"),
               networks=dict(source=f"W14 build at commit {B.BUILD_COMMIT[:8]} (results_project/v4w14/builds/main, PYTHONHASHSEED=0); registered in RUN_PLAN_HPC_V4.md section 1 and BATCH_DEF.json",
                             files=nets, registered=B.REGISTERED_SHA, registered_bytes=B.REGISTERED_BYTES, v4_meta=d.get("v4_meta"), no_365x24h=True),
               zero_slack_check=dict(file="ZERO_SLACK_CHECK.json", passed=zsc["passed"], rule=zsc["rule"], per_network={x["label"]: dict(passed=x["passed"], verdicts=x["verdicts"], bunker=x["bunker"].get("passed")) for x in zsc["networks"]}),
               environment=dict(lock="env/ENV_LOCK.txt", explicit="env/conda_explicit_linux64.txt", pip_only="env/pip_only.txt", reuse="the HPC environment already installed (HPR / v3 / v3.1): preflight env section (env_check key packages identical) - no reinstall needed", check="env/env_check.py",
                                download_bytes=env["download_bytes"], conda_packages=env["conda_packages"], same_lock_as="third batch (M10P), packages v7-v9, v3, v3.1"),
               run=dict(plan="RUN_PLAN_HPC_V4.md", definition="BATCH_DEF.json", runner="run_batch4.sh (V4 D1 copy of the v3.1 runner: package COMMIT into RUN.json and the solve receipt; --only per job; POST_ONLY=1 batch job)",
                        preflight=["preflight.sh (V4 W14 copy of the v3.1 preflight + the D1 switch-set / network-metadata check; in-job without the licence section)", "hpc/hpr_preflight_login.sh"], pack="pack_results.sh",
                        status="hpc/hpr_status.sh (V4 D1: objective incl. the constant and objective_lp)", run_dirs=B.RUN_DIRS, jobs=B.HPC_JOBS, pairs={p: list(v) for p, v in B.pairs().items()},
                        limits_status=B.LIMITS_STATUS, time_limit_s=B.TIME_LIMIT_S, wall_cap_s=B.WALL_CAP_S, licence_gap_s=B.LICENCE_GAP_S, wait_start_max_s=B.WAIT_START_MAX_S, build_timeout_s=B.BUILD_TIMEOUT_S,
                        smoke=B.SMOKE, smoke_expected_objective=B.SMOKE_EXPECTED_OBJECTIVE,
                        thresholds=dict(memory_stop_fraction=B.MEMORY_STOP_FRACTION, projection_fraction=B.PROJECTION_FRACTION, iterations_reference={k: v["iterations_reference"] for k, v in B.RUNS.items()}),
                        solve_mode="split (process 1 s2_solve.py --split-stage build, process 2 b4_split_solve.py, process 3 s2_solve.py --split-stage assign)",
                        licence="GRB_LICENSE_FILE=$HOME/.gurobi/gurobi.lic placed by the user; never in the package; referenced only by the jobs"),
               consistency=dict(file="HPC_CONSISTENCY.json", all_consistent=cons["all_consistent"], rows=len(cons["rows"])),
               operator_guide="HPC_OPERATOR_GUIDE_V4.md", facts="HPC_FACTS_20261026.md (queue limits); v3.1 run-time facts in RUN_PLAN_HPC_V4.md section 2",
               reference_values="REFERENCE_VALUES.json (numbers only: v3.1 2920x3h HPC F1 / F2, the v4 D2c local 56-snapshot smoke, the v3.1 local 56-snapshot regression)",
               never_included=["licence", "cutout", "LP / solution arrays", "365x24h networks", "results", "account / host / connection information"]),
          open(os.path.join(dist, "HPC_PACKAGE_MANIFEST.json"), "w"), indent=1)
print("manifest:", len(rows), "files,", total, "bytes; limits", B.LIMITS_STATUS, "; run dirs", B.RUN_DIRS, "; jobs", [j["name"] for j in B.HPC_JOBS.values()])
P
du -sb "$DIST"
