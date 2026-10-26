#!/bin/bash
# DFX v3 F0 (code map, read-only w.r.t. the repository): run the v1 build flow (same command as M08b, base-commit code), the solve path up to the LP
# (--stop-before-solve, single process and split process 1) and the 56-snapshot post-processing chain on a COPY of the M08b supplement-01 smoke
# solution, each with the module recorder (PYTHONPATH sitecustomize) so that the modules actually imported are listed. No solver call: the licence
# variable points to a non-existent file. Outputs: main checkout results_project/dfx_v3/{builds_v1,f0_trace,post_f0}.
set -u
WT=/home/jin/wt_dfx_v3_20261026; MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
OUT=$MAIN/results_project/dfx_v3; TRD=$OUT/f0_trace; B1=$OUT/builds_v1; PO=$OUT/post_f0; ST=$TRD/STATUS.txt
export PYTHONPATH=/home/jin/dfx3/trace; export DFX_TRACE_OUT=$TRD/modules.jsonl
export GRB_LICENSE_FILE=/nonexistent/no_licence_in_F0.lic
mkdir -p $TRD $B1 $PO; : > $DFX_TRACE_OUT
log() { echo "$1:$(date -u +%Y-%m-%dT%H:%M:%SZ)${2:+:$2}" >> $ST; }
cd $WT || exit 1
log START "commit=$(git rev-parse HEAD):dirty=$(git status --porcelain --untracked-files=no scripts_project configs research_inputs | wc -l)"
# ---- 1. builds (v1 code at the base commit; writes 2920x3h + 365x24h per scenario)
for t in integrated disconnected; do
  mkdir -p $B1/$t
  DFX_TRACE_TAG=build_$t /usr/bin/time -v $PY scripts_project/s2_network.py --scenario $t --output $B1/$t > $B1/${t}_build.log 2> $B1/${t}_build.err
  log BUILD_$t "exit=$?:$(tail -1 $B1/${t}_build.log | cut -c1-100):$(grep -h 'Maximum resident' $B1/${t}_build.err | tr -s ' '):$(grep -h 'Elapsed' $B1/${t}_build.err | tr -s ' ')"
done
# ---- 2. solve path to the LP (no solver): single process and split process 1, truncated to 56 snapshots
NET=$B1/integrated/integrated_2920_3h_unsolved.nc; COSTS=$B1/integrated/costs_active_research.csv
mkdir -p $TRD/solve_sbs $TRD/solve_split
DFX_TRACE_TAG=solve_stop_before_solve $PY scripts_project/s2_solve.py --repo . --network $NET --scenario integrated --output $TRD/solve_sbs --label SMOKE_TEST_ONLY \
  --solver gurobi --solver-profile formal_barrier_1e6_t16 --scaling on --time-limit 100 --costs-table $COSTS --truncate 56 --stop-before-solve > $TRD/solve_sbs.log 2> $TRD/solve_sbs.err
log SOLVE_SBS "exit=$?:$(tail -1 $TRD/solve_sbs.log | cut -c1-100)"
DFX_TRACE_TAG=solve_split_build $PY scripts_project/s2_solve.py --repo . --network $NET --scenario integrated --output $TRD/solve_split --label SMOKE_TEST_ONLY \
  --solver gurobi --solver-profile formal_barrier_1e6_t16 --scaling on --time-limit 100 --costs-table $COSTS --truncate 56 --split-stage build > $TRD/solve_split.log 2> $TRD/solve_split.err
log SOLVE_SPLIT "exit=$?:$(tail -1 $TRD/solve_split.log | cut -c1-100)"
# ---- 3. post-processing chain on a copy of the real 56x3h smoke solution (M08b supplement 01, ec80668f networks)
SM=$MAIN/results_project/m08b/smoke_s01; NETS=$MAIN/results_project/m08b/builds_s01
for sc in integrated disconnected; do
  rm -rf $PO/$sc; cp -r $SM/$sc $PO/$sc
  for f in VIOLATIONS.json PRECISION.json PRECISION.md V6_ACCEPTANCE.json ALLOCATION.json; do rm -f $PO/$sc/$f; done
  rm -rf $PO/$sc/m12_owen
  d=$PO/$sc; net=$NETS/$sc/${sc}_2920_3h_unsolved.nc
  DFX_TRACE_TAG=post_violations_$sc /usr/bin/time -v $PY scripts_project/l23_violation_analysis.py --repo . --solve-dir $d --network $net --scenario $sc --label SMOKE_TEST_ONLY \
    --out $d/VIOLATIONS.json --truncate 56 > $d/f0_violations.log 2> $d/f0_violations.err; log VIOLATIONS_$sc "exit=$?"
  DFX_TRACE_TAG=post_c1_$sc /usr/bin/time -v $PY scripts_project/s4o_c1_precision.py run --repo . --solve-dir $d --network $net --scenario $sc --label SMOKE_TEST_ONLY \
    --violations $d/VIOLATIONS.json --truncate 56 --reference $SM/BATCH_REFERENCE.json > $d/f0_c1.log 2> $d/f0_c1.err; log C1_$sc "exit=$?"
  DFX_TRACE_TAG=post_m12_$sc /usr/bin/time -v $PY scripts_project/m12_allocation.py run --repo . --solve-dir $d --scenario $sc --label F0_$sc --out $d --register > $d/f0_m12.log 2> $d/f0_m12.err; log M12_$sc "exit=$?"
  DFX_TRACE_TAG=post_owen_$sc /usr/bin/time -v $PY scripts_project/m12_rhs_audit.py audit --repo . --network $net --scenario $sc --solve-dir $d --allocation $d/ALLOCATION.json \
    --tag F0_$sc --out $d/m12_owen --register-dir $d --truncate 56 > $d/f0_owen.log 2> $d/f0_owen.err; log OWEN_$sc "exit=$?"
  DFX_TRACE_TAG=post_ledger_redo_$sc /usr/bin/time -v $PY scripts_project/s4d_ledger_redo.py --repo . --solve-dir $d --into $d/ledger_redo > $d/f0_ledger.log 2> $d/f0_ledger.err; log LEDGER_$sc "exit=$?"
  DFX_TRACE_TAG=post_gates_$sc $PY scripts_project/v5/gates_v6.py accept --solve-dir $d --build-receipt $NETS/$sc/${sc}_BUILD_RECEIPT.json --repo . --out $d/V6_ACCEPTANCE.json > $d/f0_v6.log 2> $d/f0_v6.err
  log V6_$sc "exit=$?:$(tail -1 $d/f0_v6.log)"
  DFX_TRACE_TAG=post_stopclass_$sc $PY scripts_project/m10_batch3_summary.py stop-class --dir $d > $d/f0_stopclass.log 2>&1; log STOPCLASS_$sc "exit=$?"
done
DFX_TRACE_TAG=post_reference $PY scripts_project/s4o_c1_precision.py reference --integrated $PO/integrated --disconnected $PO/disconnected --out $PO/BATCH_REFERENCE.json > $PO/f0_reference.log 2>&1; log REFERENCE "exit=$?"
# ---- 4. variants (batch phase 0) and the batch summary helpers
mkdir -p $PO/variants
DFX_TRACE_TAG=variants $PY scripts_project/m08a_variants.py --help > $PO/variants/help.log 2>&1; log VARIANTS_HELP "exit=$?"
log DONE
echo DONE >> $ST
