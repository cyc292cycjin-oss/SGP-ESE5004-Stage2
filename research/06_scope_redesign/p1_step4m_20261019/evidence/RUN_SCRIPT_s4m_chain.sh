#!/bin/bash
# S4M-1 + S4M-2 chain (S4M instruction; user authorisation 2026-10-19 12:12 SGT covers the local 56x3h smoke x3): at the committed S4M-0/1 code (clean tree)
#  1. four networks (2920x3h + 365x24h): integrated STEPS, disconnected STEPS, integrated NZE, disconnected gap diagnostic -> results_project/s4m/s4m1/builds
#  2. S4I audit (static + follow-ups) on the 365x24h networks and the S4K-2 style review against the S4K-2 networks / audit (read only)
#  3. biomass ratio / pool slack checks against the S4K-3 networks (s4l_5_data.py compare: 0.980 for BN / SG / VN, slack >= 0)
#  4. S4M-2 smoke: integrated STEPS, disconnected STEPS, integrated NZE, 56x3h, profile A, 30 min stop-loss each, no retry, serial; STOP on the first non-optimal
#     or gate failure (no further runs)
#  5. summary (s4m_2_summary.py)
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
B=results_project/s4m/s4m1; mkdir -p $B/builds $B/networks $B/audit $B/review
S=results_project/s4m/s4m2; mkdir -p $S/solves
ST=$B/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)" >> $ST
build() { local tag=$1 sc=$2; shift 2; mkdir -p $B/builds/$tag
  /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $sc --output $B/builds/$tag "$@" > $B/builds/${tag}_build.log 2> $B/builds/${tag}_build.err
  echo "BUILD_$tag:$?:$(tail -1 $B/builds/${tag}_build.log | cut -c1-80):$(grep -h 'Maximum resident' $B/builds/${tag}_build.err | tr -s ' '):$(grep -h 'Elapsed' $B/builds/${tag}_build.err | tr -s ' '):daily=$(ls $B/builds/$tag/*_365_24h_unsolved.nc 2>/dev/null | wc -l)" >> $ST
  grep -h "Error\|Traceback" $B/builds/${tag}_build.err | tail -3 >> $ST; }
build integrated integrated
build disconnected disconnected
build integrated_nze integrated --override fuels.price_scenario=nze
build disconnected_gap disconnected --gap-diagnostic
cp $B/builds/integrated/integrated_365_24h_unsolved.nc $B/networks/integrated_365_24h_unsolved.nc
cp $B/builds/disconnected/disconnected_365_24h_unsolved.nc $B/networks/disconnected_365_24h_unsolved.nc
cp $B/builds/integrated_nze/integrated_365_24h_unsolved.nc $B/networks/integrated_nze_365_24h_unsolved.nc
cp $B/builds/disconnected_gap/disconnected_gap_diagnostic_365_24h_unsolved.nc $B/networks/disconnected_gap_diagnostic_365_24h_unsolved.nc
cp $B/builds/integrated/integrated_BUILD_RECEIPT.json $B/networks/integrated_BUILD_RECEIPT.json
cp $B/builds/disconnected/disconnected_BUILD_RECEIPT.json $B/networks/disconnected_BUILD_RECEIPT.json
cp $B/builds/integrated_nze/integrated_BUILD_RECEIPT.json $B/networks/integrated_nze_BUILD_RECEIPT.json
cp $B/builds/disconnected_gap/disconnected_gap_diagnostic_BUILD_RECEIPT.json $B/networks/disconnected_gap_diagnostic_BUILD_RECEIPT.json
$PY scripts_project/s4i_static_audit.py --networks $B/networks --out $B/audit/static > $B/audit_static.log 2>&1; echo "AUDIT_STATIC:$?" >> $ST
$PY scripts_project/s4i_followups.py --networks $B/networks --out $B/audit/followups > $B/audit_followups.log 2>&1; echo "AUDIT_FOLLOWUPS:$?" >> $ST
(cd scripts_project && $PY s4k_2_review.py --ref-audit ../results_project/s4k/s4k2/audit --audit ../$B/audit --ref-networks ../results_project/s4k/s4k2/networks \
   --networks ../$B/networks --out ../$B/review > ../$B/review.log 2>&1); echo "REVIEW_VS_S4K2:$?" >> $ST
grep -h "Error\|Traceback" $B/review.log | tail -3 >> $ST
(cd scripts_project && $PY s4l_5_data.py compare --s4k ../results_project/s4k/s4k3/builds --diag ../$B/builds --out ../$B > ../$B/biomass_check.log 2>&1); echo "BIOMASS_CHECK:$?" >> $ST
grep -v "PROJ\|FutureWarning\|warn(" $B/biomass_check.log | tail -12 >> $ST
(cd scripts_project && $PY s4l_1_data.py compare --s4k ../results_project/s4l/s4l6/builds --s4l ../$B/builds --out ../$B > ../$B/compare_vs_s4l6.log 2>&1); echo "COMPARE_VS_S4L6:$?" >> $ST
grep -v "PROJ\|FutureWarning\|warn(" $B/compare_vs_s4l6.log | tail -3 >> $ST
echo "BUILDS_DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
# ---------------- S4M-2 smoke
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
ST2=$S/STATUS.txt
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l) profile:formal_barrier" >> $ST2
AUTH="S4M-2 (decisions 114-116, user 2026-10-19 12:12 SGT; S4M instruction S4M-2): main settings dust_cleanup on + biomass_overflow_cap_share 0.98, 56x3h smoke only, Gurobi formal_barrier, stop-loss 30 min, no retry"
run_watch() { local tag=$1 bt=$2 sc=$3; local net=$B/builds/$bt/${sc}_2920_3h_unsolved.nc d=$S/solves/$tag
  [ -f $net ] || { echo "SKIP_$tag:no build" >> $ST2; echo none; return; }
  mkdir -p $d
  /usr/bin/time -v $PY scripts_project/s2_solve.py --network $net --scenario $sc --output $d --truncate 56 --label SMOKE_TEST_ONLY \
     --authorization "$AUTH; run $tag" --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 1750 > $d.solve.log 2> $d.solve.err &
  local pid=$! start=$(date +%s)
  while kill -0 $pid 2>/dev/null; do sleep 15; if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill $pid; sleep 5; kill -9 $pid 2>/dev/null; echo "KILLED_30MIN_$tag" >> $ST2; fi; done
  wait $pid 2>/dev/null
  local cond=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition','none'))" $d/SOLVE_RECEIPT.json 2>/dev/null || echo none)
  local tol=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('all_passed_solver_tolerances'))" $d/V5_GATES.json 2>/dev/null || echo none)
  echo "RUN_$tag:$cond:$(( $(date +%s) - start ))s:tol=$tol:$(grep -h 'Maximum resident' $d.solve.err | tr -s ' ')" >> $ST2
  if [ "$cond" != "optimal" ]; then tail -40 $d/GUROBI_LOG_SCRUBBED.txt 2>/dev/null > $d/LOG_TAIL_NONOPTIMAL.txt; tail -40 $d.solve.err | grep -viE "licen[cs]e|registered|wls|academic|secret|token|accessid" > $d/STDERR_TAIL_NONOPTIMAL.txt; fi
  echo "$cond:$tol"
}
for spec in "s4m_A_integrated:integrated:integrated" "s4m_A_disconnected:disconnected:disconnected" "s4m_A_integrated_nze:integrated_nze:integrated"; do
  IFS=: read tag bt sc <<< "$spec"
  r=$(run_watch $tag $bt $sc | tail -1); c=${r%%:*}; t=${r##*:}
  echo "GATE_$tag:termination=$c:all_passed_solver_tolerances=$t" >> $ST2
  if [ "$c" != "optimal" ] || [ "$t" != "True" ]; then echo "STOP_$tag:$c:$t (S4M stop condition: smoke non-optimal or gates not passed; remaining runs not started, no retry)" >> $ST2; echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST2; grep -v PROJ $ST2; exit 1; fi
done
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST2
(cd scripts_project && $PY s4m_2_summary.py --smoke ../$S --s4k3 ../results_project/s4k/s4k3 --s4l2 ../results_project/s4l/s4l2 --s4l5 ../results_project/s4l/s4l5 > ../$S/summary.log 2>&1); echo "SUMMARY:$?" >> $ST2
grep -v PROJ $ST2
