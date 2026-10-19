#!/bin/bash
# S4M supplement 01, S4M-S2 point 2 (authorised 2026-10-19 12:28 SGT): ONE re-run of the 56x3h integrated STEPS smoke with the export-only changes of
# s2_solve.py (assign_all_duals, DUALS_BY_CONSTRAINT.nc, cost breakdown, EXPORTS.json), profile A, 30 min stop-loss, no retry. Same network as S4M-2
# (results_project/s4m/s4m1/builds/integrated). Then the S4M-S1 checklist on the S4M-2 run (before) and on this run (after), and the objective comparison.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
B=results_project/s4m/s4m1/builds; S=results_project/s4m/s4ms2; mkdir -p $S/solves $S/checklist
ST=$S/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l) profile:formal_barrier" >> $ST
AUTH="S4M supplement 01 S4M-S2 (user 2026-10-19 12:28 SGT): one 56x3h integrated STEPS smoke re-run with export-only changes (assign_all_duals, DUALS_BY_CONSTRAINT.nc, cost breakdown), Gurobi formal_barrier, stop-loss 30 min, no retry"
tag=s4m_A_integrated_rerun; d=$S/solves/$tag; mkdir -p $d
/usr/bin/time -v $PY scripts_project/s2_solve.py --network $B/integrated/integrated_2920_3h_unsolved.nc --scenario integrated --output $d --truncate 56 --label SMOKE_TEST_ONLY \
   --authorization "$AUTH" --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 1750 --costs-table $B/integrated/costs_active_research.csv > $d.solve.log 2> $d.solve.err &
pid=$!; start=$(date +%s)
while kill -0 $pid 2>/dev/null; do sleep 15; if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill $pid; sleep 5; kill -9 $pid 2>/dev/null; echo "KILLED_30MIN_$tag" >> $ST; fi; done
wait $pid 2>/dev/null
cond=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition','none'))" $d/SOLVE_RECEIPT.json 2>/dev/null || echo none)
tol=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('all_passed_solver_tolerances'))" $d/V5_GATES.json 2>/dev/null || echo none)
echo "RUN_$tag:$cond:$(( $(date +%s) - start ))s:tol=$tol:$(grep -h 'Maximum resident' $d.solve.err | tr -s ' ')" >> $ST
$PY - >> $ST 2>&1 <<EOF
import json
a = json.load(open("results_project/s4m/s4m2/solves/s4m_A_integrated/SOLVE_RECEIPT.json")); b = json.load(open("$d/SOLVE_RECEIPT.json"))
print("OBJECTIVE_COMPARE: s4m2", a.get("objective"), "rerun", b.get("objective"), "rel_diff", (b["objective"] / a["objective"] - 1) if (a.get("objective") and b.get("objective")) else None, "lp", a.get("lp", {}).get("num_row"), b.get("lp", {}).get("num_row"))
print("EXPORTS:", json.dumps(b.get("exports"))); print("DUALS:", json.dumps(b.get("duals"))); print("COST_BREAKDOWN:", json.dumps({k: v for k, v in (b.get("cost_breakdown") or {}).items() if k in ("extendable", "matched", "matched_share", "by_rule")}))
EOF
ls -la $d/DUALS_BY_CONSTRAINT.nc $d/COMPONENT_COST_BREAKDOWN.csv $d/EXPORTS.json 2>&1 | awk '{print "FILE", $5, $9}' >> $ST
(cd scripts_project && $PY s4m_s1_check.py --solve ../results_project/s4m/s4m2/solves/s4m_A_integrated --costs ../$B/integrated/costs_active_research.csv --out ../$S/checklist/S4M_S1_CHECKLIST_before.json > ../$S/checklist/before.log 2>&1); echo "CHECK_BEFORE:$?" >> $ST
(cd scripts_project && $PY s4m_s1_check.py --solve ../$d --out ../$S/checklist/S4M_S1_CHECKLIST_after.json > ../$S/checklist/after.log 2>&1); echo "CHECK_AFTER:$?" >> $ST
grep -v "PROJ\|FutureWarning\|warn(" $S/checklist/after.log | head -12 >> $ST
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
grep -v PROJ $ST
