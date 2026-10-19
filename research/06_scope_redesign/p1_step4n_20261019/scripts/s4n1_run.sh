#!/bin/bash
# S4N-1 (S4N instruction v1; user authorisation 2026-10-19 ~14:00 SGT: "S4N-1 本机 56x3h 一次运行"): ONE local 56x3h integrated STEPS solve, profile A
# (formal_barrier), with the PACKAGED code snapshot (COMMIT f50c8850, /home/jin/s4n_local/pkg/repo) and the packaged solve entry point
# (repo/scripts_project/s2_solve.py, called as run_365x24h.sh calls it: cd repo, setsid /usr/bin/time, --repo, --costs-table), so that the duals are
# written IN THE RUN (s4m_duals.write_duals) - no offline reconstruction. Network: the S4M-1 2920x3h integrated build, truncated to 56 snapshots
# exactly as in S4M-2 / S4M-S2 (same LP). 30 min stop-loss (process group), no retry, no parameter change, no warm start.
# Afterwards the read-only acceptance check (s4n1_check.py) runs; it does not call the solver.
set -u
PKG=/home/jin/s4n_local/pkg; REPO=$PKG/repo
RM=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
NET=$RM/results_project/s4m/s4m1/builds/integrated/integrated_2920_3h_unsolved.nc
COSTS=$PKG/networks/integrated_costs_active_research.csv
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
S=$RM/results_project/s4n/s4n1; D=$S/solve
mkdir -p "$S"; [ -e "$D" ] && { echo "solve dir $D exists - refusing (no second run without a new authorisation)"; exit 2; }; mkdir "$D"
ST=$S/STATUS.txt
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
SCRUB='licen[cs]e|registered[[:space:]]+to|wls(access|secret)|academic'
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) pkg_commit:$(cat $PKG/COMMIT) profile:formal_barrier net_sha256:$(sha256sum $NET | cut -c1-16) costs_sha256:$(sha256sum $COSTS | cut -c1-16) build_costs_sha256:$(sha256sum $RM/results_project/s4m/s4m1/builds/integrated/costs_active_research.csv | cut -c1-16)" >> $ST
pgrep -af "gurobi|s2_solve" | grep -v pgrep >> $ST && { echo "REFUSED: another solver process is running" >> $ST; exit 2; }
AUTH="S4N-1 (user 2026-10-19, S4N instruction v1): one local 56x3h integrated STEPS solve with the packaged code f50c8850 and the in-run dual export (write_duals), Gurobi formal_barrier, stop-loss 30 min, no retry"
( cd "$REPO" && exec setsid /usr/bin/time -v "$PY" "$REPO/scripts_project/s2_solve.py" --repo "$REPO" --network "$NET" --scenario integrated --output "$D" --truncate 56 \
    --label SMOKE_TEST_ONLY --authorization "$AUTH" --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 1750 --costs-table "$COSTS" > "$S/solve.log" 2> "$S/solve.err" ) &
pid=$!; start=$(date +%s); sleep 1; pg=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' '); [ -n "$pg" ] || pg=$pid
echo "SOLVE:pid=$pid:pgid=$pg:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
killed=0
while kill -0 $pid 2>/dev/null; do
  sleep 10
  if [ $(( $(date +%s) - start )) -ge 1800 ]; then echo "KILLED_30MIN:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST; kill -TERM -- "-$pg" 2>/dev/null; sleep 20; kill -KILL -- "-$pg" 2>/dev/null; killed=1; break; fi
done
wait $pid 2>/dev/null
w=0; while pgrep -g "$pg" >/dev/null 2>&1 && [ $w -lt 120 ]; do sleep 1; w=$((w + 1)); done
cond=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition','none'))" $D/SOLVE_RECEIPT.json 2>/dev/null || echo none)
echo "RUN:$cond:$(( $(date +%s) - start ))s:killed=$killed:$(grep -h 'Maximum resident' $S/solve.err | tr -s ' \t' ' ')" >> $ST
grep -viE "$SCRUB" "$S/solve.log" > "$S/solve_log_scrubbed.txt"; grep -viE "$SCRUB" "$S/solve.err" | tail -80 > "$S/solve_err_tail_scrubbed.txt"
echo "SOLVE_FINISHED:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
cd $RM && $PY /mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4n_20261019/scripts/s4n1_check.py --solve $D --out $S/S4N1_CHECK.json > $S/check.log 2>&1; echo "CHECK:$?" >> $ST
grep -v "PROJ\|FutureWarning\|warn(" $S/check.log | tail -40 >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
grep -v PROJ $ST
