#!/bin/bash
# B4P A5.4: local dry run of package v7 (no Gurobi: GRB_LICENSE_FILE removed; the no-solve modes point it to a non-existent file; no cloud, no upload).
#   STEP=pre      unpack v7 into /home/jin/b4p_dry/pkg; preflight guards (clean + a negative check), sha / networks / env / profile / code / tools; resources (information; fails locally)
#   STEP=build    BUILD_ONLY=1 on the TRUNCATED networks (TRUNCATE=56): process 1 of both runs (real s2_solve.py --split-stage build), BUILD_CHECK.json, no solver
#   STEP=real     the batch on truncated networks with F1 = the REAL split result C2 (lp/, split/ copied; process 2 = no-op stand-in; process 3 real) and F2 = the real
#                 M08b smoke disconnected result as an ended run (resume path): real post-processing, batch reference, regrade, B6, summary, packs -> DONE
#   STEP=synth    the batch with the stand-in process 2 (zero arrays) for both runs: real process 1 / 3 and post-processing on a synthetic solution; the
#                 classification path (G2 / C1 failures of a zero solution -> STOP) and the halted packs
#   STEP=guards   the formal command with a leftover test hook is refused
set -u
W=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_b4p_20261026; DIST=${DIST:-$W/cloud_package_dist_b4}; E=$W/evidence/dryrun
D=/home/jin/b4p_dry; PKG=$D/pkg; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
RES=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project; FAKE=/home/jin/wt_b4p_20261026/tests/research/fixtures/b4p_fake_pipeline.py
mkdir -p "$E"
busy() { ps -eo args= | grep -E '[s]2_solve\.py|[b]4_split_solve\.py' | grep -vcE '^(/usr/bin/)?time |^setsid |^env '; }
t0=$(date +%s)
case "${STEP:?pre|build|real|synth|guards}" in
  pre)
    [ -e "$D" ] && { echo "exists $D"; exit 2; }
    mkdir -p "$D" && cp -r "$DIST" "$PKG" || exit 1
    cd "$PKG"
    env -u GRB_LICENSE_FILE -u ALLOW_UNREGISTERED -u BUILD_ONLY -u POST_ONLY -u DRY -u TRUNCATE -u SOLVE_MODE PY=$PY PREFLIGHT_ONLY=guards bash preflight.sh > "$E/PREFLIGHT_GUARDS.txt" 2>&1; echo "PREFLIGHT_GUARDS_EXIT $?" >> "$E/PREFLIGHT_GUARDS.txt"
    env -u GRB_LICENSE_FILE PY=$PY PREFLIGHT_ONLY=guards SPLIT_CMD="python x" bash preflight.sh > "$E/PREFLIGHT_GUARDS_NEG.txt" 2>&1; echo "PREFLIGHT_GUARDS_NEG_EXIT $? (SPLIT_CMD left in the shell: must FAIL)" >> "$E/PREFLIGHT_GUARDS_NEG.txt"
    env -u GRB_LICENSE_FILE PY=$PY PREFLIGHT_ONLY=sha,networks,env,profile,code,tools bash preflight.sh > "$E/PREFLIGHT.txt" 2>&1; echo "PREFLIGHT_EXIT $?" >> "$E/PREFLIGHT.txt"
    env -u GRB_LICENSE_FILE PY=$PY PREFLIGHT_ONLY=resources bash preflight.sh > "$E/PREFLIGHT_RESOURCES_LOCAL.txt" 2>&1; echo "PREFLIGHT_RESOURCES_EXIT $? (local machine, information only: expected to fail)" >> "$E/PREFLIGHT_RESOURCES_LOCAL.txt"
    cp "$PKG/PREFLIGHT_BASE_CHECK.json" "$PKG/PREFLIGHT_ENV_CHECK.json" "$E/" 2>/dev/null
    echo "repo files: $(find $PKG/repo -type f | wc -l); research/ present: $([ -e $PKG/repo/research ] && echo yes || echo no)" | tee "$E/REPO_LAYOUT.txt"
    cat "$E/PREFLIGHT_GUARDS.txt" "$E/PREFLIGHT_GUARDS_NEG.txt" "$E/PREFLIGHT.txt" "$E/PREFLIGHT_RESOURCES_LOCAL.txt";;
  build)
    cd "$PKG" || exit 1; [ "$(busy)" = 0 ] || { echo "solve process running"; exit 3; }
    O=$PKG/runs/build_only; [ -e "$O" ] && { echo "exists $O"; exit 2; }
    env -u GRB_LICENSE_FILE PY=$PY ALLOW_UNREGISTERED=1 BUILD_ONLY=1 TRUNCATE=56 RUN_DIR=$O bash run_batch4.sh > "$D/build_only.out" 2>&1; echo "RUNNER_EXIT $? $(( $(date +%s) - t0 ))s" >> "$D/build_only.out"
    mkdir -p "$E/build_only"; cp "$O/STATUS.txt" "$E/build_only/STATUS.txt"; cp "$D/build_only.out" "$E/build_only/"
    for r in F1 F2; do mkdir -p "$E/build_only/$r"; for f in RUN.json BUILD_CHECK.json SOLVE_RECEIPT.json split/SPLIT_BUILD.json; do [ -f "$O/$r/$f" ] && cp "$O/$r/$f" "$E/build_only/$r/"; done; grep -hE "Maximum resident|Elapsed \(wall" "$O/$r/p1.err" > "$E/build_only/$r/p1_time.txt" 2>/dev/null; done
    tail -12 "$O/STATUS.txt";;
  real)
    cd "$PKG" || exit 1; [ "$(busy)" = 0 ] || { echo "solve process running"; exit 3; }
    O=$PKG/runs/dry_real; [ -e "$O" ] && { echo "exists $O"; exit 2; }
    mkdir -p "$O/F1" "$O/F2"
    C2=$RES/b4p/solves/c2_int56_split_A
    cp -r "$C2/lp" "$O/F1/"; mkdir -p "$O/F1/split"; cp "$C2/split/SPLIT_BUILD.json" "$C2/split/SPLIT_SOLVE.json" "$C2/split/"*_raw.npy "$O/F1/split/"; cp "$C2/gurobi.linopy.log" "$O/F1/"
    "$PY" - "$O/F1" "$C2" <<'P'
import json, sys
from pathlib import Path
o, c2 = Path(sys.argv[1]), Path(sys.argv[2])
rec = json.loads((c2 / "SOLVE_RECEIPT.json").read_text())   # the C2 receipt (after process 3); keep the build-stage view: the runner's process 3 rewrites it
keep = {k: rec[k] for k in ("label", "scenario", "authorization", "solver", "started_epoch", "stage", "transmission_losses", "dust_cleanup", "solver_profile", "scaling", "input_network", "lp", "config_subset", "solver_parameters", "parameter_source") if k in rec}
keep.update(optimize_calls=0, retry=False, split=dict(stage="build", problem_file=str(o / "split" / "problem.lp"), problem_bytes=rec["split"].get("problem_sha256_build") and 94383392, problem_sha256=rec["split"].get("problem_sha256_build")), decision="SPLIT_BUILT_SMOKE_TEST_ONLY")
(o / "SOLVE_RECEIPT.json").write_text(json.dumps(keep, indent=2))
sb = json.loads((o / "split" / "SPLIT_BUILD.json").read_text()); sb["problem_file"] = str(o / "split" / "problem.lp"); (o / "split" / "SPLIT_BUILD.json").write_text(json.dumps(sb, indent=2))
P
    S=$RES/m08b/smoke_s01/disconnected   # F2: an ENDED single-process run (resume path): the real M08b smoke result
    for f in SOLVE_RECEIPT.json V5_GATES.json INTERIOR_CHECKS.json BUNKER_ACCOUNT.json EXPORTS.json GUROBI_LOG_SCRUBBED.txt RESOURCE.jsonl CO2_FLOWS.json EMISSIONS_BY_COUNTRY.json CAPACITY_BY_TECH_COUNTRY.json cross_border_flows.csv COMPONENT_COST_BREAKDOWN.csv COMPONENT_COST_BREAKDOWN_SUMMARY.json costs_active_research.csv DUALS_INDEX.csv COUNTRY_COST_LEDGER.csv COUNTRY_COST_LEDGER_DETAIL.csv COUNTRY_COST_LEDGER_USD2020.csv LEDGER_IDENTITY.json NODAL_PRICES.csv capacity_reduced_costs.csv nodal_prices_summary.csv gurobi.linopy.log; do [ -f "$S/$f" ] && cp "$S/$f" "$O/F2/"; done
    mkdir -p "$O/F2/v5"; cp "$S/v5/kkt_summary.json" "$O/F2/v5/" 2>/dev/null; ln -s "$S/disconnected_SMOKE_TEST_ONLY_solved.nc" "$O/F2/"; ln -s "$S/DUALS_BY_CONSTRAINT.nc" "$O/F2/"; ln -s "$S/lp" "$O/F2/lp"; ln -s "$S/solution" "$O/F2/solution"
    date -u +%Y-%m-%dT%H:%M:%SZ > "$O/F2/.started"; echo optimal > "$O/F2/.cond"; echo 0 > "$O/F2/.exit"; date -u +%Y-%m-%dT%H:%M:%SZ > "$O/F2/.ended"; date +%s > "$O/F2/.solve_end"
    env -u GRB_LICENSE_FILE PY=$PY ALLOW_UNREGISTERED=1 TRUNCATE=56 RUN_DIR=$O GRB_LICENSE_FILE=/nonexistent/dry LICENCE_GAP_S=1 MONITOR_S=5 P1_WINDOW_S=10 CORES=25 SPLIT_CMD="$PY $FAKE split-solve" FAKE_OUT=$O \
      GUROBI_TIME_LIMIT_S=1750 WALL_CAP_S=1800 POST_TIMEOUT_S=1800 bash run_batch4.sh --auth "B4P local dry run (no solver: process 2 is a no-op stand-in on the real C2 result)" > "$D/dry_real.out" 2>&1; echo "RUNNER_EXIT $? $(( $(date +%s) - t0 ))s" >> "$D/dry_real.out"
    mkdir -p "$E/dry_real"; cp "$O/STATUS.txt" "$E/dry_real/"; cp "$D/dry_real.out" "$E/dry_real/"; cp "$O"/BATCH4_SUMMARY.* "$O/BATCH_REFERENCE.json" "$O/P1_DECISION.json" "$E/dry_real/" 2>/dev/null; ls "$O"/results_*.tar.gz > "$E/dry_real/PACKS.txt" 2>/dev/null
    for r in F1 F2; do mkdir -p "$E/dry_real/$r"; for f in SOLVE_RECEIPT.json V6_ACCEPTANCE.json V6_ACCEPTANCE_PROVISIONAL.json PRECISION.json STOP_CLASS.json EXPORTS.json; do [ -f "$O/$r/$f" ] && cp "$O/$r/$f" "$E/dry_real/$r/"; done; done
    tail -25 "$O/STATUS.txt";;
  synth)
    cd "$PKG" || exit 1; [ "$(busy)" = 0 ] || { echo "solve process running"; exit 3; }
    O=$PKG/runs/dry_synth; [ -e "$O" ] && { echo "exists $O"; exit 2; }
    env -u GRB_LICENSE_FILE PY=$PY ALLOW_UNREGISTERED=1 TRUNCATE=56 RUN_DIR=$O GRB_LICENSE_FILE=/nonexistent/dry LICENCE_GAP_S=1 MONITOR_S=5 P1_WINDOW_S=10 CORES=25 SPLIT_CMD="$PY $FAKE split-solve" FAKE_OUT=$O FAKE_SLEEP=20 \
      GUROBI_TIME_LIMIT_S=1750 WALL_CAP_S=1800 POST_TIMEOUT_S=1800 bash run_batch4.sh --auth "B4P local dry run (synthetic zero solution from the stand-in process 2)" > "$D/dry_synth.out" 2>&1; echo "RUNNER_EXIT $? $(( $(date +%s) - t0 ))s" >> "$D/dry_synth.out"
    mkdir -p "$E/dry_synth"; cp "$O/STATUS.txt" "$E/dry_synth/"; cp "$D/dry_synth.out" "$E/dry_synth/"; cp "$O"/BATCH4_SUMMARY.* "$O/STOP" "$O/UNUSABLE" "$O/PROJECTION_F1.json" "$O/P1_DECISION.json" "$E/dry_synth/" 2>/dev/null; ls "$O"/results_*.tar.gz > "$E/dry_synth/PACKS.txt" 2>/dev/null
    for r in F1 F2; do mkdir -p "$E/dry_synth/$r"; for f in SOLVE_RECEIPT.json V6_ACCEPTANCE.json STOP_CLASS.json BUILD_CHECK.json; do [ -f "$O/$r/$f" ] && cp "$O/$r/$f" "$E/dry_synth/$r/"; done; grep -hE "Maximum resident|Elapsed \(wall" "$O/$r/p1.err" "$O/$r/p3.err" > "$E/dry_synth/$r/times.txt" 2>/dev/null; done
    tail -25 "$O/STATUS.txt";;
  guards)
    cd "$PKG" || exit 1
    env -u ALLOW_UNREGISTERED -u BUILD_ONLY GRB_LICENSE_FILE=/nonexistent/dry PY=$PY SPLIT_CMD="python x" RUN_DIR=$PKG/runs/guard_test bash run_batch4.sh --auth "x" > "$E/GUARDS_REFUSAL.txt" 2>&1; echo "EXIT $? (must be 2 REFUSED)" >> "$E/GUARDS_REFUSAL.txt"
    env -u ALLOW_UNREGISTERED GRB_LICENSE_FILE=/nonexistent/dry PY=$PY SOLVE_MODE=single RUN_DIR=$PKG/runs/guard_test bash run_batch4.sh --auth "x" >> "$E/GUARDS_REFUSAL.txt" 2>&1; echo "EXIT $? (must be 2 REFUSED: SOLVE_MODE)" >> "$E/GUARDS_REFUSAL.txt"
    env -u ALLOW_UNREGISTERED GRB_LICENSE_FILE=/nonexistent/dry PY=$PY BUILD_ONLY=1 RUN_DIR=$PKG/runs/guard_test bash run_batch4.sh --auth "x" >> "$E/GUARDS_REFUSAL.txt" 2>&1; echo "EXIT $? (must be 2 REFUSED: --auth with BUILD_ONLY)" >> "$E/GUARDS_REFUSAL.txt"
    [ -e "$PKG/runs/guard_test" ] && echo "RUN_DIR CREATED (unexpected)" >> "$E/GUARDS_REFUSAL.txt"
    cat "$E/GUARDS_REFUSAL.txt";;
esac
echo "$(( $(date +%s) - t0 )) s $STEP" >> "$E/TIME_$STEP.txt"
