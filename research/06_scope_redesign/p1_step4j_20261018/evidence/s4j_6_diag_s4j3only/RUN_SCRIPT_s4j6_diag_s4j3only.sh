#!/bin/bash
# S4J-6 isolation diagnostic 2 (user authorisation 2026-10-18, S4J_STOP_01 section 6 item 1): the same smoke with --override demand.nonindustrial_electricity=astar_residual and network.transmission_losses=none
# (network = S4H + S4J-3), profile A, 56x3h, integrated only, one run, no other parameter change, no retry; 30 min stop-loss.
cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
export GRB_LICENSE_FILE=/home/jin/gurobi.lic
OUT=results_project/s4j/s4j6_diag_s4j3only; mkdir -p $OUT/builds $OUT/solves
ST=$OUT/STATUS.txt; : > $ST
echo "START:$(date -u +%Y-%m-%dT%H:%M:%SZ) commit:$(git rev-parse --short HEAD) dirty:$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l) profile:formal_barrier override:demand.nonindustrial_electricity=astar_residual,network.transmission_losses=none" >> $ST
AUTH="S4J-6 isolation diagnostic 2 (user 2026-10-18: S4J_STOP_01 section 6 item 1 - same smoke with demand.nonindustrial_electricity=astar_residual and network.transmission_losses=none, network = S4H + S4J-3, profile A, 56x3h, integrated only, one run, diagnosis only, no other parameter change)"
echo "NOTE: a first start at 13:02:01Z was stopped during the network build (wrong authorisation text in the run script), before any solve" >> $ST
mkdir -p $OUT/builds/integrated
/usr/bin/time -v $PY scripts_project/s2_network.py --scenario integrated --output $OUT/builds/integrated --no-daily --override demand.nonindustrial_electricity=astar_residual --override network.transmission_losses=none > $OUT/builds/integrated_build.log 2> $OUT/builds/integrated_build.err
echo "BUILD_integrated:$?:$(tail -1 $OUT/builds/integrated_build.log | cut -c1-60):$(grep -h 'Maximum resident' $OUT/builds/integrated_build.err | tr -s ' ')" >> $ST
net=$OUT/builds/integrated/integrated_2920_3h_unsolved.nc; d=$OUT/solves/integrated
[ -f $net ] || { echo "NO_BUILD" >> $ST; cat $ST; exit 1; }
mkdir -p $d
/usr/bin/time -v $PY scripts_project/s2_solve.py --network $net --scenario integrated --output $d --truncate 56 --label SMOKE_TEST_ONLY \
   --authorization "$AUTH" --solver gurobi --solver-profile formal_barrier --scaling on --time-limit 1750 > $d.solve.log 2> $d.solve.err &
pid=$!; start=$(date +%s)
while kill -0 $pid 2>/dev/null; do sleep 15; if [ $(( $(date +%s) - start )) -ge 1800 ]; then kill $pid; sleep 5; kill -9 $pid 2>/dev/null; echo "KILLED_30MIN_integrated" >> $ST; fi; done
wait $pid 2>/dev/null
cond=$($PY -c "import json,sys; print(json.load(open(sys.argv[1])).get('termination_condition','none'))" $d/SOLVE_RECEIPT.json 2>/dev/null || echo none)
echo "RUN_integrated:$cond:$(( $(date +%s) - start ))s:$(grep -h 'Maximum resident' $d.solve.err | tr -s ' ')" >> $ST
if [ "$cond" != "optimal" ]; then tail -40 $d/GUROBI_LOG_SCRUBBED.txt 2>/dev/null > $d/LOG_TAIL_NONOPTIMAL.txt; tail -40 $d.solve.err | grep -viE "licen[cs]e|registered|wls|academic|secret|token|accessid" > $d/STDERR_TAIL_NONOPTIMAL.txt; fi
echo "DONE:$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $ST
grep -v PROJ $ST
