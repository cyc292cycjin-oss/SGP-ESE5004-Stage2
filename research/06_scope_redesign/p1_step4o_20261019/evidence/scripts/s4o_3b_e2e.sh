#!/bin/bash
# S4O supplement 01 S4O-3' (decision 121; user authorisation 2026-10-19 with the supplement: ONE local 56x3h run, 30 min stop-loss, no retry):
# end-to-end check of the S4O run pipeline - the package run script run_365x24h.sh (commit $1) with its automatic C1 step - on the S4M-1 integrated
# 2920x3h build truncated to 56 snapshots (TRUNCATE=56 -> --truncate 56, label SMOKE_TEST_ONLY), profile A by default, integrated STEPS only.
# Local package-like folder: repo = git archive of the commit (+ .package_commit), networks/integrated_365_24h_unsolved.nc = symlink to the S4M-1 2920x3h
# build, the build cost table; no licence content is read or copied (GRB_LICENSE_FILE only referenced).
set -u
WANT=${1:?commit (8 chars)}
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=$RM/results_project/s4m/s4m1/builds/integrated; P=/home/jin/s4o_local/pkg_e2e
cd $RM
[ "$(git rev-parse --short=8 HEAD)" = "$WANT" ] || { echo "REFUSED: HEAD is not $WANT"; exit 2; }
[ "$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" = 0 ] || { echo "REFUSED: dirty tree"; exit 2; }
ps -eo cmd | grep -qE '[s]2_solve.py|[g]urobi_cl' && { echo "REFUSED: solver process running"; exit 2; }
[ ! -e $P ] || { echo "REFUSED: $P exists"; exit 2; }
mkdir -p $P/repo $P/networks
git archive HEAD | tar x -C $P/repo; git rev-parse HEAD > $P/COMMIT; cp $P/COMMIT $P/repo/.package_commit
cp $RM/research/06_scope_redesign/p1_step4o_20261019/cloud_package/run_365x24h.sh $RM/research/06_scope_redesign/p1_step4o_20261019/cloud_package/preflight.sh $P/
ln -s $B/integrated_2920_3h_unsolved.nc $P/networks/integrated_365_24h_unsolved.nc
cp $B/costs_active_research.csv $P/networks/integrated_costs_active_research.csv
echo "network (2920x3h build, truncated in the run): $(sha256sum $B/integrated_2920_3h_unsolved.nc | cut -c1-16)"
cd $P
( PREFLIGHT_ONLY=profile,c1,versions,tools PY=$PY bash preflight.sh serial ) 2>&1 | tail -12
TRUNCATE=56 GUROBI_TIME_LIMIT_S=1750 WALL_CAP_S=1800 MONITOR_S=10 GRB_LICENSE_FILE=/home/jin/gurobi.lic PY=$PY \
  bash run_365x24h.sh --mode serial --runs integrated --auth "S4O supplement 01 S4O-3' (decision 121; user 2026-10-19): one local 56x3h end-to-end check of the S4O pipeline, profile A, stop-loss 30 min, no retry" \
  > $P/run_stdout.txt 2>&1
echo "RUN_SCRIPT_EXIT:$?"
cat $P/runs/*/STATUS.txt | cut -c1-300
echo "E2E_DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)"
