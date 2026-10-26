#!/bin/bash
# DFX v3 F6.3: local dry run of run_dfx.sh (no solver call; GRB_LICENSE_FILE tripwire = non-existent file). Networks staged flat as the package
# lays them out (symlinks to results_project/dfx_v3/builds_v2). Three parts: (1) BUILD_ONLY on the FULL 365x24h networks without any test switch
# (registered checks on: the formal path except the solve), (2) BUILD_ONLY with the test switches TRUNCATE=56 ALLOW_UNREGISTERED=1 (the instruction's
# truncated dry run), (3) refusals: the formal command with a switch left in the shell, unregistered values, no-solve mode with --auth. Writes
# results_project/dfx_v3/dry_run_v8/DRY_RUN_DFX.json (code_commit, passed, build_check per run) for make_package_dfx.sh.
set -u
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=$MAIN/results_project/dfx_v3/builds_v2; D=$MAIN/results_project/dfx_v3/${1:-dry_run_v8}; PKG=$WT/research/06_scope_redesign/p1_dfx_20261026/cloud_package_dfx
n=$(ps -eo args= | grep -E '[s]2_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '); [ "$n" = 0 ] || { echo "REAL SOLVE RUNNING ($n)"; exit 4; }
mkdir -p $D/networks; cd $WT || exit 1
for sc in integrated disconnected; do
  ln -sfn $B/$sc/${sc}_365_24h_unsolved.nc $D/networks/${sc}_365_24h_unsolved.nc; ln -sfn $B/$sc/${sc}_BUILD_RECEIPT.json $D/networks/${sc}_BUILD_RECEIPT.json
  ln -sfn $B/$sc/costs_active_research.csv $D/networks/${sc}_costs_active_research.csv
done
cp $PKG/run_dfx.sh $PKG/preflight_dfx.sh $D/; cp research/06_scope_redesign/p1_m10p_20261022/cloud_package/pack_results.sh $D/; cp research/06_scope_redesign/p1_dfx_20261026/BATCH3_REFERENCE_VALUES.json $D/
git rev-parse HEAD > $D/COMMIT
export PY REPO=$WT NETS=$D/networks PYTHONHASHSEED=0
env -u ALLOW_UNREGISTERED -u TRUNCATE -u GUROBI_TIME_LIMIT_S -u WALL_CAP_S -u LICENCE_GAP_S -u GRB_LICENSE_FILE true
echo "== part 1: BUILD_ONLY, full 365x24h networks, registered path (no switch)"; t0=$(date +%s)
( export RUN_DIR=$D/full; BUILD_ONLY=1 bash $D/run_dfx.sh ); rc1=$?; echo "part1 exit=$rc1 $(( $(date +%s) - t0 ))s"; tail -4 $D/full/STATUS.txt
echo "== part 2: BUILD_ONLY, TRUNCATE=56, ALLOW_UNREGISTERED=1 (test switches)"; t0=$(date +%s)
( export RUN_DIR=$D/trunc; BUILD_ONLY=1 TRUNCATE=56 ALLOW_UNREGISTERED=1 bash $D/run_dfx.sh ); rc2=$?; echo "part2 exit=$rc2 $(( $(date +%s) - t0 ))s"; tail -4 $D/trunc/STATUS.txt
echo "== part 3: refusals (formal command with leftovers; licence path non-existent so nothing can start)"
R=$D/refusals; mkdir -p $R; : > $R/REFUSALS.txt
try() { local name=$1; shift; local out; out=$(env "$@" GRB_LICENSE_FILE=/nonexistent/lic RUN_DIR=$R/$name bash $D/run_dfx.sh --auth "dry-run refusal test" 2>&1); local rc=$?; echo "$name exit=$rc :: $(echo "$out" | head -1 | cut -c1-160)" >> $R/REFUSALS.txt; [ -f $R/$name/STATUS.txt ] && echo "$name STATUS WRITTEN (unexpected)" >> $R/REFUSALS.txt; }
try truncate_left TRUNCATE=56
try hook_left SOLVE_CMD="python x"
try fake_left FAKE_SLEEP_V1=9
try time_limit_override GUROBI_TIME_LIMIT_S=100
try wall_override WALL_CAP_S=100
try gap_override LICENCE_GAP_S=1
try build_only_with_auth BUILD_ONLY=1
try post_only_with_auth POST_ONLY=1
try dry_with_auth DRY=1
out=$(env GRB_LICENSE_FILE=/nonexistent/lic RUN_DIR=$R/no_lic bash $D/run_dfx.sh --auth "x" 2>&1); echo "no_licence_file exit=$? :: $(echo "$out" | head -1 | cut -c1-160)" >> $R/REFUSALS.txt
out=$(env GRB_LICENSE_FILE=$D/COMMIT RUN_DIR=$R/no_auth bash $D/run_dfx.sh 2>&1); echo "no_auth exit=$? :: $(echo "$out" | head -1 | cut -c1-160)" >> $R/REFUSALS.txt
cat $R/REFUSALS.txt
$PY - $D "$(git rev-parse HEAD)" <<'P'
import json, sys, time
from pathlib import Path
D = Path(sys.argv[1]); commit = sys.argv[2]
bc = {}; ok = True
for part in ("full", "trunc"):
    for rid in ("V1", "V2"):
        p = D / part / rid / "BUILD_CHECK.json"; j = json.load(open(p)) if p.exists() else None
        bc[f"{part}:{rid}"] = (dict(passed=j["passed"], failed=[k for k, v in j["checks"].items() if not v], lp=j["lp"], peak_rss_gib=round(j["peak_rss_gib"], 2), snapshots=None, network_sha256=j["network_sha256"]) if j else dict(passed=False, missing=True))
        ok = ok and bool(j and j["passed"])
st = {part: (D / part / "STATUS.txt").read_text().splitlines() for part in ("full", "trunc")}
ok = ok and all(any(l.startswith("DONE:") for l in v) for v in st.values())
ref = [l for l in (D / "refusals" / "REFUSALS.txt").read_text().splitlines()]
ref_ok = all((" exit=2 " in l) and ("STATUS WRITTEN" not in l) for l in ref) and len(ref) == 11
res = dict(code_commit=commit, passed=bool(ok and ref_ok), build_check={rid: v for k, v in bc.items() if k.startswith("full:") for rid in [k.split(":")[1]]},
           build_check_truncated={k.split(":")[1]: v for k, v in bc.items() if k.startswith("trunc:")}, refusals=ref, refusals_all_exit_2=ref_ok,
           status_full=[l for l in st["full"] if l.split(":")[0] in ("START", "BASE_CHECK", "PHASE_1", "BUILD_CHECK_V1", "BUILD_CHECK_V2", "SUMMARY", "PACK_final", "DONE")],
           status_trunc=[l for l in st["trunc"] if l.split(":")[0] in ("START", "BASE_CHECK", "PHASE_1", "BUILD_CHECK_V1", "BUILD_CHECK_V2", "DONE")],
           licence="GRB_LICENSE_FILE tripwire = /nonexistent (no-solve modes); no Gurobi call", written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), solver_runs=0)
(D / "DRY_RUN_DFX.json").write_text(json.dumps(res, indent=1) + "\n")
print("DRY_RUN passed:", res["passed"], "| build_check full:", {k: v.get("passed") for k, v in res["build_check"].items()}, "| trunc:", {k: v.get("passed") for k, v in res["build_check_truncated"].items()}, "| refusals ok:", ref_ok)
for k, v in res["build_check"].items():
    print(k, v.get("lp"), "peak", v.get("peak_rss_gib"), "failed", v.get("failed"))
P
