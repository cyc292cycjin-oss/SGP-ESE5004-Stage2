#!/bin/bash
# DFX v3 F0 part 2: the solve path up to the LP only (--stop-before-solve single process; --split-stage build), no solver call.
set -u
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=$MAIN/results_project/dfx_v3; TRD=$OUT/f0_trace; B1=$OUT/builds_v1; ST=$TRD/STATUS.txt
export PYTHONPATH=/home/jin/dfx3/trace; export DFX_TRACE_OUT=$TRD/modules.jsonl
export GRB_LICENSE_FILE=/nonexistent/no_licence_in_F0.lic
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
cd $WT || exit 1
NET=$B1/integrated/integrated_2920_3h_unsolved.nc; COSTS=$B1/integrated/costs_active_research.csv
AUTH="DFX v3 F0 code map: LP build only (--stop-before-solve / --split-stage build), no solver call, licence variable points to a non-existent file"
rm -rf $TRD/solve_sbs $TRD/solve_split; mkdir -p $TRD/solve_sbs $TRD/solve_split
DFX_TRACE_TAG=solve_stop_before_solve /usr/bin/time -v $PY scripts_project/s2_solve.py --repo . --network $NET --scenario integrated --output $TRD/solve_sbs --label SMOKE_TEST_ONLY --authorization "$AUTH" \
  --solver gurobi --solver-profile formal_barrier_1e6_t16 --scaling on --time-limit 100 --costs-table $COSTS --truncate 56 --stop-before-solve > $TRD/solve_sbs.log 2> $TRD/solve_sbs.err
log SOLVE_SBS2 "exit=$?:$(tail -1 $TRD/solve_sbs.log | cut -c1-100):$(grep -h 'Maximum resident' $TRD/solve_sbs.err | tr -s ' ')"
DFX_TRACE_TAG=solve_split_build /usr/bin/time -v $PY scripts_project/s2_solve.py --repo . --network $NET --scenario integrated --output $TRD/solve_split --label SMOKE_TEST_ONLY --authorization "$AUTH" \
  --solver gurobi --solver-profile formal_barrier_1e6_t16 --scaling on --time-limit 100 --costs-table $COSTS --truncate 56 --split-stage build > $TRD/solve_split.log 2> $TRD/solve_split.err
log SOLVE_SPLIT2 "exit=$?:$(tail -1 $TRD/solve_split.log | cut -c1-100):$(grep -h 'Maximum resident' $TRD/solve_split.err | tr -s ' ')"
echo DONE2 >> $ST
